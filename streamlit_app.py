def process_pdf_jd(session, uploaded_file):
    description = extract_text_from_pdf(uploaded_file)
    if not description:
        raise ValueError("Could not extract text from the JD PDF.")
    
    title = os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
    
    skills_list = [line.strip() for line in description.split('\n') if len(line.strip()) > 15 and len(line.strip()) < 80][:12]
    if not skills_list:
        skills_list = [title]

    jd_embedding = create_embeddings([description])[0]
    dummy_vec = [0.0] * 768

    new_JD = JD(
        title=title,
        description=description,
        required_skills=skills_list,
        preferred_skills=[],
        preferred_education=[],
        responsibilities=["General responsibilities per job description"],
        domain=["General"],
        industries=["Technology"],
        embedding=jd_embedding,
        responsibilities_embedding=jd_embedding,
        education_embedding=dummy_vec,
        domain_embedding=dummy_vec,
        industries_embedding=dummy_vec,
        required_skills_embeddings=dummy_vec,
        preferred_skills_embeddings=dummy_vec
    )
    session.add(new_JD)
    session.commit()
    session.refresh(new_JD)
    
    jd_skills_data = []
    for skill in skills_list:
        skill_vec = create_embeddings([skill])[0]
        jd_skills_data.append({
            "jd_id": new_JD.id,
            "skill": skill,
            "skill_embedding": skill_vec
        })
    if jd_skills_data:
        session.execute(Jd_Skill.__table__.insert(), jd_skills_data)
        session.commit()
    return new_JD.id, title
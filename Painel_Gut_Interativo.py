with aba2:
    st.subheader("Matriz GUT - Priorização das Dores (Treemap)")

    score_max_padrao = int(df_gut['Score'].max())
    if 'reset_filtros' in st.session_state and st.session_state['reset_filtros']:
        st.session_state['score_gut_range'] = (0, score_max_padrao)

    score_min, score_max = st.slider(
        "Filtro por Score GUT", 
        0, score_max_padrao, 
        st.session_state.get('score_gut_range', (0, score_max_padrao)), 
        key='score_gut_range'
    )

    df_gut_filtrado = df_gut[(df_gut['Score'] >= score_min) & (df_gut['Score'] <= score_max)].copy()
    st.dataframe(df_gut_filtrado, use_container_width=True)

    # Garante que as labels sejam strings seguras com score formatado
    df_gut_filtrado['Label'] = df_gut_filtrado.apply(lambda row: f"{row['Problema']} = {int(row['Score'])}", axis=1)

    fig_gut = go.Figure(go.Treemap(
        labels=df_gut_filtrado['Label'],
        parents=[""] * len(df_gut_filtrado),
        values=df_gut_filtrado['Score'],
        textinfo="label",
        textfont=dict(size=54),
        hovertext=df_gut_filtrado.apply(
            lambda row: f"Gravidade: {row['Gravidade']}<br>"
                        f"Urgência: {row['Urgência']}<br>"
                        f"Tendência: {row['Tendência']}<br>"
                        f"Score: {row['Score']}", 
            axis=1
        ),
        hoverinfo="text",
        marker=dict(
            colors=df_gut_filtrado['Score'],
            colorscale=[[0.0, 'green'], [0.5, 'yellow'], [1.0, 'red']],
            cmin=score_min,
            cmax=score_max,
            showscale=True
        )
    ))

    fig_gut.update_layout(
        title="Treemap - Priorização GUT",
        margin=dict(l=10, r=10, t=50, b=10),
        height=600
    )

    st.plotly_chart(fig_gut, use_container_width=True)

    gut_buf = BytesIO()
    fig_gut.write_image(gut_buf, format="png")
    st.download_button(
        "🖕️ Baixar Treemap GUT", 
        data=gut_buf.getvalue(), 
        file_name="treemap_gut.png", 
        mime="image/png"
    )

    # Exporta tabela com bordas para PDF se necessário
    if 'gerar_pdf_gut_com_borda' in st.session_state and st.session_state['gerar_pdf_gut_com_borda']:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(60, 8, "Problema", border=1)
        pdf.cell(25, 8, "Gravidade", border=1)
        pdf.cell(25, 8, "Urgência", border=1)
        pdf.cell(25, 8, "Tendência", border=1)
        pdf.cell(25, 8, "Score", border=1)
        pdf.ln()

        pdf.set_font("Arial", "", 9)
        for _, row in df_gut_filtrado.iterrows():
            pdf.cell(60, 8, str(row['Problema'])[:30], border=1)
            pdf.cell(25, 8, str(row['Gravidade']), border=1)
            pdf.cell(25, 8, str(row['Urgência']), border=1)
            pdf.cell(25, 8, str(row['Tendência']), border=1)
            pdf.cell(25, 8, str(row['Score']), border=1)
            pdf.ln()

    # Exporta tabela do plano de ação com bordas para PDF se necessário
    if 'gerar_pdf_plano_com_borda' in st.session_state and st.session_state['gerar_pdf_plano_com_borda'] and 'df_filtrado' in locals():
        pdf.set_font("Arial", "B", 10)
        pdf.cell(90, 8, "Ação", border=1)
        pdf.cell(40, 8, "Responsável", border=1)
        pdf.cell(30, 8, "Prazo", border=1)
        pdf.ln()

        pdf.set_font("Arial", "", 9)
        for _, row in df_filtrado.iterrows():
            if row['Prazo'] == '15 dias':
                pdf.set_fill_color(139, 0, 0)  # vermelho escuro
            elif row['Prazo'] == '30 dias':
                pdf.set_fill_color(255, 99, 71)  # vermelho claro
            elif row['Prazo'] == '60 dias':
                pdf.set_fill_color(255, 165, 0)  # laranja
            elif row['Prazo'] == '90 dias':
                pdf.set_fill_color(0, 128, 0)  # verde
            else:
                pdf.set_fill_color(255, 255, 255)  # branco padrão

            pdf.cell(90, 8, str(row['Ação'])[:45], border=1, fill=True)
            pdf.cell(40, 8, str(row['Responsável']), border=1, fill=True)
            pdf.cell(30, 8, str(row['Prazo']), border=1, fill=True)
            pdf.ln()

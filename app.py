from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Preluam valorile introduse de utilizator
        try:
            MV_kb = int(request.form.get('MV_kb'))
            MO_kb = int(request.form.get('MO_kb'))
            page_kb = int(request.form.get('page_kb'))
        except ValueError:
            error = "Valorile introduse trebuie să fie numere întregi."
            return render_template('index.html', error=error)

        MV_bytes = MV_kb * 1024
        MO_bytes = MO_kb * 1024
        page_size_bytes = page_kb * 1024

        num_pages_virtual = MV_bytes // page_size_bytes
        num_pages_physical = MO_bytes // page_size_bytes

        if num_pages_virtual == 0:
            error = "Memoria virtuală este prea mică pentru dimensiunea unei pagini."
            return render_template('index.html', error=error)

        if num_pages_physical == 0:
            error = "Memoria fizică este prea mică pentru dimensiunea unei pagini."
            return render_template('index.html', error=error)

        # Generăm tabelul de pagini virtuale
        table = []
        for i in range(num_pages_virtual):
            start_addr = i * page_size_bytes
            end_addr = start_addr + page_size_bytes - 1
            table.append((None, i, start_addr, end_addr, None))

        # Mergem la pagina de introducere a MV_Page și MO_Page
        return render_template('pages_input.html', 
                               MV_kb=MV_kb, MO_kb=MO_kb, page_kb=page_kb,
                               page_size_bytes=page_size_bytes,
                               num_pages_virtual=num_pages_virtual,
                               num_pages_physical=num_pages_physical,
                               table=table)
    return render_template('index.html')


@app.route('/compute', methods=['POST'])
def compute():
    try:
        MV_kb = int(request.form.get('MV_kb'))
        MO_kb = int(request.form.get('MO_kb'))
        page_kb = int(request.form.get('page_kb'))
        page_size_bytes = page_kb * 1024

        num_pages_virtual = int(request.form.get('num_pages_virtual'))
        num_pages_physical = int(request.form.get('num_pages_physical'))
    except ValueError:
        return "Eroare la conversia datelor."

    # Reconstruim tabelul inițial
    table = []
    for i in range(num_pages_virtual):
        start_addr = i * page_size_bytes
        end_addr = start_addr + page_size_bytes - 1
        table.append((None, i, start_addr, end_addr, None))

    # Preluam MV_Page și MO_Page de la utilizator
    for i in range(num_pages_virtual):
        mv_page_num = request.form.get(f'mv_page_{i}')
        try:
            mv_page_num = int(mv_page_num)
        except ValueError:
            return "MV_Page trebuie să fie număr întreg!"
        old = table[i]
        table[i] = (mv_page_num, old[1], old[2], old[3], old[4])

    for i in range(num_pages_physical):
        mo_page_num = request.form.get(f'mo_page_{i}')
        try:
            mo_page_num = int(mo_page_num)
        except ValueError:
            return "MO_Page trebuie să fie număr întreg!"
        old = table[i]
        table[i] = (old[0], old[1], old[2], old[3], mo_page_num)

    for i in range(num_pages_physical, num_pages_virtual):
        old = table[i]
        table[i] = (old[0], old[1], old[2], old[3], None)

    # Adresa virtuală
    try:
        address = int(request.form.get('address'))
    except ValueError:
        return "Adresa trebuie să fie număr întreg!"

    virtual_page_index = None
    page_start_addr = None
    for (mv_pg, v_idx, start_addr, end_addr, mo_pg) in table:
        if start_addr <= address <= end_addr:
            virtual_page_index = v_idx
            page_start_addr = start_addr
            break

    if virtual_page_index is None:
        return "Adresa nu se află în spațiul virtual!"

    # Deplasare
    displacement = address - page_start_addr

    # Determinăm paginile MV și MO
    mv_page_num = None
    mo_page_num_val = None
    for (mv_pg, v_idx, start_addr, end_addr, mo_pg) in table:
        if v_idx == virtual_page_index:
            mv_page_num = mv_pg
            mo_page_num_val = mo_pg
            break

    # Calcul adresa MV
    mv_address = mv_page_num * page_size_bytes + displacement

    # Calcul adresa MO
    mo_target_start = None
    for (mv_pg2, v_idx2, start_addr2, end_addr2, mo_pg2) in table:
        # În codul original se pare că e o mică confuzie,
        # se caută MO_Page == virtual_page_index, dar noi avem mo_pg ca index, nu clar.
        # Presupunem că mo_pg2 este indexul virtual al paginii fizice.
        # Mai logic ar fi mo_pg2 să indice pagina virtuală mapată în pagina fizică.
        # Dacă mo_pg2 == virtual_page_index, atunci această pagină MO corespunde paginii virtuale.
        if mo_pg2 == virtual_page_index:
            mo_target_start = start_addr2
            break

    # Dacă nu am găsit o pagină fizică asociată, adresa MO nu poate fi calculată
    mo_address = mo_target_start + displacement if mo_target_start is not None else None

    return render_template('result.html',
                           table=table,
                           address=address,
                           virtual_page_index=virtual_page_index,
                           displacement=displacement,
                           mv_address=mv_address,
                           mo_address=mo_address)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7000)

with open('remote_index_debug.html', 'rb') as f:
    content = f.read()
    # Find the extract-perfil select
    pos = content.find(b'id="extract-perfil"')
    if pos != -1:
        # Print next 300 bytes
        print("BYTES AROUND extract-perfil:")
        print(content[pos:pos+300])
    else:
        print("NOT FOUND")

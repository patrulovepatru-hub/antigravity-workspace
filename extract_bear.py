# Vamos a abrir el archivo del oso, ¿vale?
# Usamos 'r' de 'read' (leer) porque solo queremos ver qué cuenta.
with open('bear.txt', 'r', encoding='utf-8') as archivo_oso:
    # Leemos todo el contenido de una, ¡pam!
    contenido = archivo_oso.read()

# Ahora pillamos solo los primeros 90 caracteres.
# Es como cortar un trozo de pastel, del principio hasta el 90.
recorte = contenido[:90]

# Y ahora lo guardamos en 'first.txt'.
# Usamos 'w' de 'write' (escribir) para crear el archivo nuevo.
with open('first.txt', 'w', encoding='utf-8') as archivo_nuevo:
    archivo_nuevo.write(recorte)

print("¡Listo, tronco! Ya tienes tus 90 caracteres en first.txt.")

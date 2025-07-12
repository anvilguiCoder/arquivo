from datetime import datetime

def validar_cpf(cpf):
    # Verifica se tem exatamente 11 dígitos numéricos
    return cpf.isdigit() and len(cpf) == 11

def validar_data(data):
    try:
        datetime.strptime(data, "%d/%m/%Y")
        return True
    except ValueError:
        return False

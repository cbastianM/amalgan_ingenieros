def parsear_moneda(v) -> float:
    """Convierte string de moneda colombiana a float."""
    if v is None:
        return 0.0
    s = str(v).strip().replace("$", "").replace(" ", "")
    if not s:
        return 0.0
    
    # Lógica para manejar formatos COP: $1.234.567 o $1,234.56
    if "." in s and "," not in s:
        partes = s.split(".")
        if len(partes) > 2 or (len(partes) == 2 and len(partes[-1]) == 3):
            s = s.replace(".", "")
    elif "," in s and "." not in s:
        partes = s.split(",")
        if len(partes) > 2 or (len(partes) == 2 and len(partes[-1]) == 3):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif "." in s and "," in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    
    try:
        return float(s)
    except ValueError:
        return 0.0

def fmt_cop(v) -> str:
    """Formatea número como moneda colombiana."""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "$0"
    return "$" + f"{n:,.0f}".replace(",", ".")

def fmt_dec(v, d: int = 2) -> str:
    """Formatea decimal con separador de miles y decimales colombiano."""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "0"
    t = f"{n:,.{d}f}"
    return t.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
def total(csv_text):
    """Sum the amount column of a bank CSV export."""
    lines = csv_text.strip().splitlines()[1:]
    return sum(float(line.split(",")[1]) for line in lines)

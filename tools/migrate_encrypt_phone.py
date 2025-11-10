from data_encryption import encrypt_data
import csv

inp = "data/employees.csv"
outp = "data/employees_encrypted.csv"

with open(inp, newline="", encoding="utf-8") as f_in, open(outp, "w", newline="", encoding="utf-8") as f_out:
    r = csv.DictReader(f_in)
    fieldnames = r.fieldnames
    w = csv.DictWriter(f_out, fieldnames=fieldnames)
    w.writeheader()
    for row in r:
        if row.get("phone") and not row["phone"].startswith("gAAAA"):  # crude Fernet marker
            row["phone"] = encrypt_data(row["phone"])
        w.writerow(row)

print("Done. Review and replace the original file after verifying.")
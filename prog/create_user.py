#!/usr/bin/env python3
"""
Helper script to create a new user with bcrypt-hashed password
and append to data/users.csv
"""

import bcrypt
import csv
import os

USERS_FILE = "../data/users.csv"  # adjust if your path differs

def create_user(username, password, role, full_name):
    # Hash the password using bcrypt
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Ensure file exists with headers
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password", "role", "full_name"])

    # Append the new user
    with open(USERS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([username, hashed, role, full_name])

    print(f"[✔] User '{username}' created successfully with role '{role}'.")

if __name__ == "__main__":
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    role = input("Enter role (admin/cafe): ").strip().lower()
    full_name = input("Enter full name: ").strip()
    create_user(username, password, role, full_name)

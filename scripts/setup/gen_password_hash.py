import getpass

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

if __name__ == "__main__":
    ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)

    password = getpass.getpass("Admin password (input hidden): ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords did not match.")

    hashed = ph.hash(password)

    try:
        ph.verify(hashed, password)
        verified = "OK"
    except VerifyMismatchError:
        verified = "FAILED"

    print(f"  Hash      : {hashed}")
    print(f"  Status    : {verified}")
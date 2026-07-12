from argon2 import PasswordHasher

if __name__ == "__main__":
    ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)

    password = "Your_Password"

    hashed = ph.hash(password)

    if ph.verify(hashed, password):
        verified = "OK"
    else:
        verified = "FAILED"

    print(f"  Password  : {password}")
    print(f"  Hash      : {hashed}")
    print(f"  Status    : {verified}")

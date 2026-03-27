from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
# EXACT HASH from VPS
hashed = '$pbkdf2-sha256$29000$2rtXKsX4n9Na670XonSOkQ$X48UM4/fBhbIdBCB7ADo26iT62jOOvB1VgBpJgbyMrE'
plain = '1304@Ev19'

try:
    res = pwd_context.verify(plain, hashed)
    print(f"Verification result: {res}")
except Exception as e:
    print(f"Error during verification: {e}")

# Try direct hash verify
from passlib.hash import pbkdf2_sha256
try:
    res2 = pbkdf2_sha256.verify(plain, hashed)
    print(f"Direct verification result: {res2}")
except Exception as e:
    print(f"Error during direct verification: {e}")

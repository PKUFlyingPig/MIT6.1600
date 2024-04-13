import hashlib
import sys

def toy_hash(x):
    # Hash bytes with SHA2
    digest  = hashlib.sha256(x).digest()

    # Use first 6 bytes
    return digest[0:6]

def main():
    # Get next password from file
    for line in sys.stdin:
        # Remove trailing newline
        password = line.strip()
       
        # Convert string to bytes
        b = password.encode('ascii')

        h = toy_hash(b)

        # Print as hex string
        print(h.hex())


if __name__ == "__main__":
    main()

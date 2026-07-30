from ai_engine import simplify_contract

print("===== EasyLegal AI =====")
print("1. Analyze Contract")
print("2. Exit")

choice = input("Enter your choice: ")

if choice == "1":
    filename = input("Enter contract file name: ")

    try:
        file = open("backend/contracts/" + filename, "r")
        text = file.read()
        simplify_contract(text)
        file.close()

    except FileNotFoundError:
        print("Contract file not found.")

elif choice == "2":
    print("Thank you for using EasyLegal AI.")

else:
    print("Invalid choice.")

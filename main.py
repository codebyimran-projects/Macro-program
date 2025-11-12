# main.py

# Import the MacroUI class from the interface.py file inside the ui folder
from ui.interface import MacroUI  

# Define the main function that will start our program
def main():
    # Create an instance of the MacroUI class
    # This initializes the GUI window and sets up all UI elements
    app = MacroUI()  
    
    # Run the GUI loop
    # This keeps the window open and responsive until the user closes it
    app.run()  

# This line ensures that this code runs only when this file is executed directly
# It prevents the code from running if this file is imported as a module in another file
if __name__ == "__main__":  
    # Call the main function to start the program
    main()  

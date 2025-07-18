import customtkinter as ctk

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VidAudDownload")
        self.geometry("580x500")
        self.resizable(False, False)

if __name__ == "__main__":
    app = App()
    app.mainloop()

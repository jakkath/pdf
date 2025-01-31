import pandas as pd

def load_metadata():
    """Load metadata from the CSV file"""
    try:
        return pd.read_csv("pdf_details.csv")
    except FileNotFoundError:
        print("⚠️ Metadata file not found. Please run the crawler first.")
        return pd.DataFrame()

def search_pdfs(query):
    """Search for PDFs based on user query"""
    metadata = load_metadata()
    if metadata.empty:
        return

    # Perform a case-insensitive search across all columns
    results = metadata[metadata.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
    
    if results.empty:
        print("🔍 No results found.")
    else:
        print("🔍 Search Results:")
        print(results[["Title", "Grade", "Subject", "Topic", "Download Link"]].to_string(index=False))

def download_pdf_by_url(url, title):
    """Download a PDF by its URL"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        filename = f"{sanitize_filename(title)}.pdf"
        filepath = os.path.join(save_folder, filename)

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        print(f"✅ Downloaded: {filename}")

    except Exception as e:
        print(f"❌ Failed to download {url}: {str(e)}")

def main_menu():
    """Main menu for the search engine"""
    while True:
        print("\n📚 PDF Search Engine")
        print("1. Search PDFs")
        print("2. Download PDF by URL")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            query = input("Enter search query: ")
            search_pdfs(query)
        elif choice == "2":
            url = input("Enter PDF download URL: ")
            title = input("Enter PDF title: ")
            download_pdf_by_url(url, title)
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("⚠️ Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
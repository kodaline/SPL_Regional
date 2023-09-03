import os

def print_folder_structure(start_path, indent=0, file_limit=5):
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent_sub = ' ' * 4 * (level - indent)

        # Ignore hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        print(f"{indent_sub}+--{os.path.basename(root)}/")
        
        # Limit the number of files to print
        for i, f in enumerate(files):
            if i >= file_limit:
                print(f"{indent_sub}    |-- ...")
                break
            print(f"{indent_sub}    |-- {f}")

if __name__ == "__main__":
    start_path = '.'  # current directory
    print(f"Folder structure for {os.path.abspath(start_path)}:")
    print_folder_structure(start_path)

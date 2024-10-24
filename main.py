import json
import requests
import urllib.request
import sys
import random
import string
from colorama import Fore

def generate_random_classname(existing_classnames):
    while True:
        first_char = random.choice(string.ascii_lowercase)
        rest = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
        classname = first_char + rest
        if classname not in existing_classnames:
            return classname

def get_classes():
    classes_file = "./tailwind-classes.json"
    try:
        with open(classes_file, "r") as file:
            tailwind_classes = json.load(file)
            return tailwind_classes
    except Exception:
        return False

def checksum_check():
    tailwind_classes = get_classes()
    checksum_url = "https://raw.githubusercontent.com/xKotelek/tailwind-to-css/refs/heads/main/tailwind-classes.json"
    
    try:
        response = requests.get(checksum_url)
        if response.ok:
            checksum = response.json()['checksum']
            if not tailwind_classes or 'checksum' not in tailwind_classes or tailwind_classes['checksum'] != checksum:
                urllib.request.urlretrieve(checksum_url, "./tailwind-classes.json")
        else:
            if not tailwind_classes or 'checksum' not in tailwind_classes:
                print(f"{Fore.RED}Cannot find tailwind classes json file and cannot download it. Please check your internet connection!{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}Checksum check failed: {e}{Fore.RESET}")

def convert(file):
    checksum_check()
    tailwind_classes_data = get_classes()

    if not tailwind_classes_data:
        return

    tailwind_classes = {cls["name"]: cls for cls in tailwind_classes_data['classes'] if "name" in cls}
    variant_types = tailwind_classes_data["variantTypes"]

    new_css_rules = {}
    converted_content = ""

    try:
        with open(file, "r") as f:
            content = f.read()

        lines = content.split("\n")

        for line in lines:
            # Usuwamy pustą klasę
            line = line.replace('class=""', '')
            line = line.replace('className=""', '')

            if 'class="' in line or 'className="' in line:
                attr_type = 'class="' if 'class="' in line else 'className="'
                class_attr_start = line.index(attr_type) + len(attr_type)
                class_attr_end = line.index('"', class_attr_start)
                classes_in_line = line[class_attr_start:class_attr_end].split()

                matched_styles = []
                remaining_classes = []
                special_rules = {"hover": [], "before": [], "after": []}

                for class_name in classes_in_line:
                    found_match = False
                    negative = class_name.startswith("-")
                    class_name = class_name[1:] if negative else class_name

                    # Obsługa hover, before, after
                    if class_name.startswith("hover:"):
                        special_rules["hover"].append(class_name[6:])
                        continue
                    elif class_name.startswith("before:"):
                        special_rules["before"].append(class_name[7:])
                        continue
                    elif class_name.startswith("after:"):
                        special_rules["after"].append(class_name[6:])
                        continue

                    for json_class_name, json_class_data in tailwind_classes.items():
                        if class_name == json_class_name:
                            value = json_class_data["value"]
                            if negative:
                                value = value.replace("{variant}", "-" + value)
                            matched_styles.append(value)
                            found_match = True
                            break

                        elif class_name.startswith(json_class_name + "-"):
                            variant_key = class_name[len(json_class_name) + 1:]
                            if "[" in variant_key and "]" in variant_key:
                                variant_value = variant_key[variant_key.index("[") + 1:variant_key.index("]")]
                                value = json_class_data["value"].replace("{variant}", variant_value)
                                if negative:
                                    value = value.replace(variant_value, "-" + variant_value)
                                matched_styles.append(value)
                                found_match = True
                                break
                            elif variant_key in variant_types.get(json_class_data["variantType"], {}):
                                variant_value = variant_types[json_class_data["variantType"]][variant_key]
                                value = json_class_data["value"].replace("{variant}", variant_value)
                                if negative:
                                    value = value.replace(variant_value, "-" + variant_value)
                                matched_styles.append(value)
                                found_match = True
                                break

                    if not found_match:
                        remaining_classes.append(class_name)

                # Generowanie klasy
                if matched_styles or remaining_classes:
                    random_classname = generate_random_classname(new_css_rules.keys())
                    new_classes_str = " ".join(remaining_classes).strip()  # Usuwamy zbędne spacje

                    # Dodajemy wygenerowaną klasę
                    line = line[:class_attr_start] + random_classname + (" " + new_classes_str if new_classes_str else "") + line[class_attr_end:]

                    if matched_styles:
                        new_css_rules[random_classname] = "\n".join(f"\t{style}" for style in matched_styles)

                # Dodawanie klas dla hover
                if special_rules["hover"]:
                    hover_styles = [tailwind_classes[cls]["value"] for cls in special_rules["hover"] if cls in tailwind_classes]
                    if hover_styles:
                        hover_classname = generate_random_classname(new_css_rules.keys())
                        new_css_rules[hover_classname + ":hover"] = "\n".join(f"\t{style}" for style in hover_styles)
                        line = line[:class_attr_end] + f' {hover_classname}' + line[class_attr_end:]  # Dodajemy hover class

                # Dodawanie klas dla before
                if special_rules["before"]:
                    before_styles = ["content: '';"]  # Zawsze dodajemy content: ''
                    before_styles += [tailwind_classes[cls]["value"] for cls in special_rules["before"] if cls in tailwind_classes]
                    if before_styles:
                        before_classname = generate_random_classname(new_css_rules.keys())
                        new_css_rules[before_classname + "::before"] = "\n".join(f"\t{style}" for style in before_styles)
                        line = line[:class_attr_end] + f' {before_classname}' + line[class_attr_end:]  # Dodajemy before class

                # Dodawanie klas dla after
                if special_rules["after"]:
                    after_styles = ["content: '';"]  # Zawsze dodajemy content: ''
                    after_styles += [tailwind_classes[cls]["value"] for cls in special_rules["after"] if cls in tailwind_classes]
                    if after_styles:
                        after_classname = generate_random_classname(new_css_rules.keys())
                        new_css_rules[after_classname + "::after"] = "\n".join(f"\t{style}" for style in after_styles)
                        line = line[:class_attr_end] + f' {after_classname}' + line[class_attr_end:]  # Dodajemy after class

            converted_content += line + "\n"  # Dodajemy linię

        # Pisanie do pliku HTML
        with open(file, "w") as f:
            f.write(converted_content)

        css_filename = f"converted-{generate_random_classname(new_css_rules.keys())}.css"
        with open(css_filename, "w") as css_file:
            css_file.write("/* Generated with tailwind-to-css by xKotelek @ https://github.com/xKotelek/tailwind-to-css */\n\n")
            for class_name, css_rule in new_css_rules.items():
                css_file.write(f".{class_name} {{\n{css_rule}\n}}\n\n")

        print(f"{Fore.GREEN}Conversion successful! {file} updated, and {css_filename} created with new classes.{Fore.RESET}")

    except Exception as e:
        print(f"{Fore.RED}An error occurred: {e}{Fore.RESET}")

def init():
    valid_extensions = ['js', 'jsx', 'ts', 'tsx', 'vue', 'html', 'htm', 'svelte', 'md', 'mdx']
    
    if len(sys.argv) < 2:
        print("Please provide a valid file. Available filetypes:")
        print(f"{Fore.GREEN}*.js, *.jsx, *.ts, *.tsx, *.vue, *.html, *.htm, *.svelte, *.md, *.mdx{Fore.RESET}")
    else:
        file = sys.argv[1]
        file_extension = file.split('.')[-1]
        
        if file_extension in valid_extensions:
            convert(file)
        else:
            print("Please provide a valid file. Available filetypes:")
            print(f"{Fore.GREEN}*.js, *.jsx, *.ts, *.tsx, *.vue, *.html, *.htm, *.svelte, *.md, *.mdx{Fore.RESET}")

init()
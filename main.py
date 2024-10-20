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
            if 'class="' in line or 'className="' in line:
                attr_type = 'class="' if 'class="' in line else 'className="'
                class_attr_start = line.index(attr_type) + len(attr_type)
                class_attr_end = line.index('"', class_attr_start)
                classes_in_line = line[class_attr_start:class_attr_end].split()

                matched_styles = []
                remaining_classes = []
                special_rules = {"hover": [], "active": [], "before": [], "after": []}

                for class_name in classes_in_line:
                    found_match = False
                    negative = False  # Flaga dla klas z minusem

                    # Sprawdzanie, czy klasa ma przedrostek "-".
                    if class_name.startswith("-"):
                        negative = True
                        class_name = class_name[1:]  # Usuwanie minusa

                    for json_class_name, json_class_data in tailwind_classes.items():
                        # Dopasowanie klasy bez wariantu
                        if class_name == json_class_name:
                            value = json_class_data["value"]
                            if negative:
                                value = value.replace("{variant}", "-" + value)
                            matched_styles.append(value)
                            found_match = True
                            break

                        # Dopasowanie klasy z wariantem
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
                        # Obsługa prefiksów hover:, active:, before:, after:
                        if class_name.startswith("hover:"):
                            special_rules["hover"].append(class_name[6:])
                        elif class_name.startswith("active:"):
                            special_rules["active"].append(class_name[7:])
                        elif class_name.startswith("before:"):
                            special_rules["before"].append(class_name[7:])
                        elif class_name.startswith("after:"):
                            special_rules["after"].append(class_name[6:])
                        else:
                            remaining_classes.append(class_name)

                if matched_styles:
                    random_classname = generate_random_classname(new_css_rules.keys())
                    remaining_classes.append(random_classname)
                    new_css_rules[random_classname] = "\n".join(f"\t{style};" for style in matched_styles)

                # Dodawanie specjalnych reguł dla hover, active, before, after
                if special_rules["hover"]:
                    random_classname = generate_random_classname(new_css_rules.keys())
                    remaining_classes.append(random_classname)
                    hover_styles = [f"\t{tailwind_classes[cls]['value']};" for cls in special_rules["hover"] if cls in tailwind_classes]
                    new_css_rules[random_classname + ":hover"] = "\n".join(hover_styles)

                if special_rules["active"]:
                    random_classname = generate_random_classname(new_css_rules.keys())
                    remaining_classes.append(random_classname)
                    active_styles = [f"\t{tailwind_classes[cls]['value']};" for cls in special_rules["active"] if cls in tailwind_classes]
                    new_css_rules[random_classname + ":active"] = "\n".join(active_styles)

                # Dodawanie once `content: '';` dla before i after
                if special_rules["before"]:
                    random_classname = generate_random_classname(new_css_rules.keys())
                    remaining_classes.append(random_classname)
                    before_styles = ["\tcontent: '';\n"] + [f"\t{tailwind_classes[cls]['value']};" for cls in special_rules["before"] if cls in tailwind_classes]
                    new_css_rules[random_classname + "::before"] = "\n".join(before_styles)

                if special_rules["after"]:
                    random_classname = generate_random_classname(new_css_rules.keys())
                    remaining_classes.append(random_classname)
                    after_styles = ["\tcontent: '';\n"] + [f"\t{tailwind_classes[cls]['value']};" for cls in special_rules["after"] if cls in tailwind_classes]
                    new_css_rules[random_classname + "::after"] = "\n".join(after_styles)

                new_classes_str = " ".join(remaining_classes)
                line = line[:class_attr_start] + new_classes_str + line[class_attr_end:]

            converted_content += line + "\n"

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

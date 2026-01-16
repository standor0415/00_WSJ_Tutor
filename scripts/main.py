from datetime import datetime
from omegaconf import DictConfig
from pathlib import Path
from utils.parse_html import parse_html
from utils.translate_study import translate_stduy

import sys
import hydra

TODAY = datetime.now().strftime("%Y-%m-%d")
PROJECT_PATH = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_PATH / "configs"


@hydra.main(version_base=None, config_path=str(CONFIG_DIR), config_name="config")
def main(cfg: DictConfig):

    print(f"Today is {TODAY}")
    print(f"Using model: {cfg.model.name}")

    date_input = input("Enter date (YYMMDD) or press Enter for today's news: ")

    if date_input:
        try:
            # Test if date is in YYMMDD format
            if len(date_input) != 6 or not date_input.isdigit():
                raise ValueError("Date must be 6 digits (e.g., 260113)")
            parsed_date = datetime.strptime(date_input, "%y%m%d")
            target_date = parsed_date.strftime("%Y-%m-%d")

        except ValueError as e:
            print(f"Wrong format: {e}")
            sys.exit(1)
    else:
        target_date = TODAY

    # Input DataPath
    input_folder_path = PROJECT_PATH / "input"

    target_articles = [
        filepath.stem for filepath in input_folder_path.glob(f"*{target_date}*.html")
    ]

    # Output DataPath
    output_folder_path = PROJECT_PATH / "output/markdown"
    processed_articles = [
        filepath.stem.replace("main", "article")
        for filepath in output_folder_path.glob(f"*{target_date}*.md")
    ]
    unprocessed = set(target_articles) - set(processed_articles)
    unprocessed_list = sorted(unprocessed)

    print("\nUnprocessed File List")
    result = "\n".join(
        [f"{i}. {filename}" for i, filename in enumerate(unprocessed_list, 1)]
    )
    print(result + "\n")

    idx = int(input("Which file do you want to translate? (e.g., 1) : ")) - 1

    target_file = input_folder_path / f"{unprocessed_list[idx]}.html"
    parsed_file = parse_html(target_file)

    translate_stduy(parsed_file, cfg)


if __name__ == "__main__":
    main()

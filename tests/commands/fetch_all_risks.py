import os
import requests
import gzip
import shutil
import argparse
import textwrap

class FetchAllRisks:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the Risks Digest scraper.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        parser.description = textwrap.dedent(
            """
            Scrape all the articles from RISKS digest and store the txt files.
            """
        )

        parser.add_argument(
            "output_directory",
            type=str,
            help="Directory to store the extracted plaintext files.",
        )

    # Function to download and extract an issue
    def download_and_extract_issue(self, volume, issue):
        # Convert issue number to a two-digit string
        issue_str = f"{issue:02d}"

        # Construct the download URL
        download_url = f"{base_url}/{volume}/risks-{volume}.{issue_str}.gz"

        # File names
        gz_filename = f"risks-V{volume}.{issue_str}.gz"
        plaintext_filename = f"{output_directory}/risks-V{volume}.{issue_str}.txt"

        # Download the gzip-compressed file
        response = requests.get(download_url)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Save the gzip-compressed file
            with open(gz_filename, "wb") as f:
                f.write(response.content)

            try:
                # Decompress the gzip file
                with gzip.open(gz_filename, 'rb') as gz_file:
                    with open(plaintext_filename, 'wb') as txt_file:
                        shutil.copyfileobj(gz_file, txt_file)

                print(f"Issue {issue_str} of Volume {volume} downloaded and extracted.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
            finally:
                # Remove the gzip file
                if os.path.exists(gz_filename):
                    os.remove(gz_filename)
        else:
            print(f"Failed to download Issue {issue_str} of Volume {volume}. Status code: {response.status_code}")

    def run(self, args: argparse.Namespace):
        # Base URL for the Risks Digest archive
        base_url = "http://catless.ncl.ac.uk/Risks/archive"

        # Directory to store the extracted plaintext files
        output_directory = args.output_directory

        # Create the output directory if it doesn't exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        for volume in range(1, 34):  # Assuming volumes are from 1 to 33
            for issue in range(1, 100):  # Assuming a maximum of 99 issues per volume
                self.download_and_extract_issue(volume, issue)
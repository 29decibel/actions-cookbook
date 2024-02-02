"""
A simple AI Action template for comparing timezones

Please checkout the base guidance on AI Actions in our main repository readme:
https://github.com/robocorp/robocorp/blob/master/README.md

"""
import os
from robocorp.actions import action
from datetime import datetime
import pytz
import pypandoc
from ebooklib import epub
import uuid

# email stuff
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# constant for kindle email
GMAIL_ADDRESS = os.environ.get('GMAIL_ADDRESS')
KINDLE_EMAIL = os.environ.get('KINDLE_EMAIL')


def send_email_with_attachment(subject, body, from_addr, to_addr, app_password, file_path):
    # SMTP server configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    # Create the email object
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the file
    with open(file_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',
                    f"attachment; filename= {file_path.split('/')[-1]}")

    # Add the attachment to the email message
    msg.attach(part)

    # Send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Secure the connection
        server.login(from_addr, app_password)  # Use your app password here
        server.send_message(msg)
        server.quit()


@action
def markdown_to_epub(title: str, markdown_text: str) -> str:
    """
    Send content to kindle email

    Args:
        markdown_text (str): markdown content to convert to epub
        title (str): title of the epub (filename will be title.epub)

    Returns:
        str: just result message
    """

    author = "Kindle GPT"
    # create output filename randomly, using uuid maybe
    output_filename = f"{uuid.uuid4()}.epub"

    # output_filename = "output.epub"
    # Convert Markdown to HTML using pypandoc
    html_content = pypandoc.convert_text(markdown_text, 'html', format='md')

    # Create an EPUB book
    book = epub.EpubBook()

    # Set the title and author
    book.set_title(title)
    book.set_language('en')
    book.add_author(author)

    # Create an EPUB chapter from HTML content
    c1 = epub.EpubHtml(title=title, file_name='chapter1.xhtml', lang='en')
    c1.content = html_content

    # Add chapter to the book
    book.add_item(c1)

    # Define Table Of Contents
    book.toc = (epub.Link('chapter1.xhtml', title, 'chapter1'),)

    # Add default NCX and Navigation file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define CSS style
    style = 'BODY {color: black;}'
    nav_css = epub.EpubItem(
        uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)

    # Add CSS file
    book.add_item(nav_css)

    # Basic spine
    book.spine = ['nav', c1]

    # Write the EPUB file
    epub.write_epub(output_filename, book, {})

    # checking if the content exists
    if os.path.exists(output_filename):
        print(f"EPUB file '{output_filename}' has been created oh yay!!!.")
        app_password = os.environ.get('GMAIL_APP_PASSWORD')
        send_email_with_attachment(
            'Subject Here',
            'Email body goes here',
            GMAIL_ADDRESS,
            KINDLE_EMAIL,
            app_password,
            output_filename
        )

    return f"'{title}' has been sent to {KINDLE_EMAIL}."


@action
def compare_time_zones(user_timezone: str, compare_to_timezones: str) -> str:
    """
    Compares user timezone time difference to given timezones

    Args:
        user_timezone (str): User timezone in tz database format. Example: "Europe/Helsinki"
        compare_to_timezones (str): Comma seperated timezones in tz database format. Example: "America/New_York, Asia/Kolkata"

    Returns:
        str: List of requested timezones, their current time and the user time difference in hours
    """
    output: list[str] = []

    try:
        user_tz = pytz.timezone(user_timezone)
        user_now = datetime.now(user_tz)
    except pytz.InvalidTimeError:
        return f"Timezone '{user_timezone}' could not be found. Use tz database format."

    output.append(
        f"- Current time in {user_timezone} is {user_now.strftime('%I:%M %p')}")

    target_timezones = [s.strip() for s in compare_to_timezones.split(',')]
    for timezone in target_timezones:
        try:
            target_tz = pytz.timezone(timezone)
            target_now = datetime.now(target_tz)
            time_diff = (int(user_now.strftime('%z')) -
                         int(target_now.strftime('%z'))) / 100

            output.append(
                f"- Current time in {timezone} is {target_now.strftime('%I:%M %p')}, the difference with {user_timezone} is {time_diff} hours")
        except pytz.InvalidTimeError:
            output.append(
                f"- Timezone '{timezone}' could not be found. Use tz database format.")

    return "\n".join(output)

"""Login模块"""

import base64
import io
import os
import random

from PIL import Image, ImageDraw, ImageFont
from pywebio.input import input, input_group
from pywebio.output import clear, put_html, put_image, put_text
from pywebio.platform.fastapi import start_server
from pywebio.session import set_env


def generate_math_captcha():
    """Generate a simple math captcha with numbers under 20"""
    num1 = random.randint(1, 20)
    num2 = random.randint(1, 20)
    operation = random.choice(["+", "-"])

    if operation == "-" and num1 < num2:
        num1, num2 = num2, num1  # Ensure positive result

    result = num1 + num2 if operation == "+" else num1 - num2
    expression = f"{num1} {operation} {num2}"

    # Create image with the math expression
    img = Image.new("RGB", (200, 100), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()

    draw.text((50, 35), expression, fill="black", font=font)

    # Convert image to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_str}", result


def login():
    """Main login page"""
    set_env(title="Master Server Login")

    # CSS styles for the login page
    style = """
    <style>
        body {
            background-color: #e6f3ff !important;
            font-family: Arial, sans-serif;
        }
        .container {
            max-width: 400px;
            margin: 50px auto;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .title {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 24px;
        }
    </style>
    """

    put_html(style)
    put_html('<div class="container">')
    put_html('<h1 class="title">Master Server Login</h1>')

    while True:
        # Generate new captcha
        captcha_image, correct_answer = generate_math_captcha()

        # Create login form
        data = input_group(
            "",
            [
                input("Username", name="username", required=True),
                input("Password", name="password", type="password", required=True),
                put_image(captcha_image),
                input(
                    "Please solve the math problem above",
                    name="captcha",
                    type="number",
                    required=True,
                ),
            ],
        )

        # Verify captcha
        if data["captcha"] != correct_answer:
            clear()
            put_html(style)
            put_html('<div class="container">')
            put_html('<h1 class="title">Master Server Login</h1>')
            put_text("Incorrect captcha answer. Please try again.")
            continue

        # Here you would typically verify the username and password
        # For now, we'll just print the values
        return data


if __name__ == "__main__":
    start_server(login, port=8080, debug=True)

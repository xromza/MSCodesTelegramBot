import subprocess
import sys
import os

def install_packages_from_file(filename="requirements.txt"):
    if not os.path.exists(filename):
        print(f"❌ Файл '{filename}' не найден.")
        return

    print("📦 Устанавливаю зависимости из requirements.txt...")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-warn-conflicts",  # для совместимости
                "-r",
                filename
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(result.stdout)
        print("✅ Все зависимости установлены успешно!")
    except subprocess.CalledProcessError as e:
        print("❌ Произошла ошибка при установке зависимостей:")
        print(e.stderr)

if __name__ == "__main__":
    install_packages_from_file()

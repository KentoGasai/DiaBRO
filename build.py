"""
Скрипт сборки PyDiab в исполняемый файл
"""
import subprocess
import sys
import os
import shutil


def get_version():
    """Запрашивает версию билда"""
    default_version = "0.1.1"
    
    print("=" * 50)
    print("  PyDiab - Сборка исполняемого файла")
    print("=" * 50)
    print()
    
    version = input(f"Введите версию билда [{default_version}]: ").strip()
    if not version:
        version = default_version
    
    return version


def check_pyinstaller():
    """Проверяет наличие PyInstaller"""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("PyInstaller не установлен. Устанавливаю...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True


def build(version):
    """Собирает exe файл"""
    print()
    print(f"Сборка версии {version}...")
    print()
    
    # Имя выходного файла
    output_name = f"PyDiab_v{version}"
    
    # Путь к главному скрипту
    main_script = "main.py"
    
    # Путь к папке с изображениями
    images_path = os.path.join("game", "images")
    
    # Команда PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # Один exe файл
        "--windowed",          # Без консольного окна
        "--name", output_name,
        # Добавляем папку с изображениями
        "--add-data", f"{images_path};game/images",
        # Иконка (если есть)
        # "--icon", "icon.ico",
        "--clean",             # Очистка перед сборкой
        "--noconfirm",         # Без подтверждений
        main_script
    ]
    
    print("Выполняю команду:")
    print(" ".join(cmd))
    print()
    
    # Запуск PyInstaller
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print()
        print("=" * 50)
        print("  Сборка завершена успешно!")
        print("=" * 50)
        print()
        print(f"Исполняемый файл: dist/{output_name}.exe")
        print()
        
        # Информация о размере
        exe_path = os.path.join("dist", f"{output_name}.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"Размер файла: {size_mb:.1f} MB")
        
        return True
    else:
        print()
        print("Ошибка сборки!")
        return False


def cleanup():
    """Очистка временных файлов"""
    print()
    clean = input("Удалить временные файлы сборки? [Y/n]: ").strip().lower()
    if clean != 'n':
        # Удаляем папку build
        if os.path.exists("build"):
            shutil.rmtree("build")
            print("Удалена папка build/")
        
        # Удаляем .spec файл
        for f in os.listdir("."):
            if f.endswith(".spec"):
                os.remove(f)
                print(f"Удалён файл {f}")


def main():
    # Проверяем, что мы в правильной директории
    if not os.path.exists("main.py"):
        print("Ошибка: Запустите скрипт из корневой папки проекта!")
        print("Файл main.py не найден.")
        sys.exit(1)
    
    # Проверяем PyInstaller
    check_pyinstaller()
    
    # Получаем версию
    version = get_version()
    
    # Собираем
    success = build(version)
    
    if success:
        cleanup()
    
    print()
    input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()


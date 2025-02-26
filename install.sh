#!/bin/bash

# Проверка, запущен ли скрипт от root
if [[ $EUID -ne 0 ]]; then
    echo "Скрипт требует root-прав. Пожалуйста, введите пароль."
    exec sudo "$0" "$@"
fi


detect_distro() {
    if command -v hostnamectl &> /dev/null; then
        os_info=$(hostnamectl | grep "Operating System" | awk -F': ' '{print tolower($2)}')
        case "$os_info" in
            *ubuntu*) echo "ubuntu" ;;
            *debian*) echo "debian" ;;
            *mos*) echo "mos" ;;
            *arch*) echo "arch" ;;
            *fedora*) echo "fedora" ;;
            *) echo "unknown" ;;
        esac
    else
        echo "unknown"
    fi
}


# Установка библиотек
install_packages() {
    case "$1" in
        ubuntu|debian|)
            apt update
            apt install -y tigervnc-standalone-server tigervnc-common git build-essential cmake

            ;;
        arch)
            pacman -Sy --noconfirm tigervnc git cmake
            ;;
        fedora|mos)
            dnf update
            dnf install -y tigervnc-server tigervnc git cmake
            ;;

        *)
            echo "Неизвестный дистрибутив."
            exit 1
            ;;
    esac
}
clone_and_build_project() {
    REPO_URL="https://github.com/nearbyx000/Helper-Utils"
    BUILD_DIR="build"

    echo "Клонируем репозиторий: $REPO_URL"
    git clone "$REPO_URL" project || {
        echo "Ошибка: не удалось клонировать репозиторий."
        exit 1
    }

    cd project || exit

    echo "Создаём директорию для сборки..."
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR" || exit

    echo "Запускаем CMake..."
    cmake .. || {
        echo "Ошибка: CMake завершился неудачей."
        exit 1
    }

    echo "Собираем проект..."
    make -j$(nproc) || {
        echo "Ошибка: сборка завершилась неудачей."
        exit 1
    }

    echo "Сборка завершена успешно!"
}

distro=$(detect_distro)
echo "Обнаружен дистрибутив: $distro"
install_dependencies $distro
clone_and_build_project

echo "Проект готов к работе" 







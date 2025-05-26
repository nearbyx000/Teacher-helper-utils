#!/bin/bash

# Проверка прав суперпользователя
if [ "$(id -u)" -ne 0 ]; then
  echo "Ошибка: Пожалуйста, запустите скрипт с правами суперпользователя (sudo)."
  exit 1
fi

# --- Функции ---

# Функция для определения дистрибутива
detect_distro() {
    if command -v hostnamectl &> /dev/null; then
        os_info=$(hostnamectl | grep "Operating System" | awk -F': ' '{print tolower($2)}')
        case "$os_info" in
            *ubuntu*) echo "ubuntu" ;;\
            *debian*) echo "debian" ;;\
            *mos*) echo "mos" ;;\
            *arch*) echo "arch" ;;\
            *fedora*) echo "fedora" ;;\
            *) echo "unknown" ;;\
        esac
    else
        echo "unknown"
    fi
}

# Функция для установки пакетов Samba
install_samba_packages() {
    local distro=$1
    echo "Проверяем и устанавливаем Samba для дистрибутива: $distro"
    case "$distro" in
        ubuntu|debian|)
            apt update && apt install -y samba samba-common samba-client || { echo "Ошибка установки Samba." ; exit 1; }
            ;;
        arch)
            pacman -Sy --noconfirm samba || { echo "Ошибка установки Samba." ; exit 1; }
            ;;
        fedora|mos)
            dnf install -y samba || { echo "Ошибка установки Samba." ; exit 1; }
            ;;
        *)
            echo "Ошибка: Неизвестный дистрибутив. Установите Samba вручную."
            exit 1
            ;;
    esac
    echo "Samba установлена."
}

# Функция для добавления пользователя в системную группу (если она существует)
add_user_to_group() {
    local user_name=$1
    local group_name=$2
    if getent group "$group_name" &>/dev/null; then
        if ! id -nG "$user_name" | grep -qw "$group_name"; then
            echo "Добавляем пользователя $user_name в группу $group_name..."
            usermod -aG "$group_name" "$user_name" || { echo "Ошибка: не удалось добавить пользователя в группу." ; exit 1; }
        else
            echo "Пользователь $user_name уже в группе $group_name."
        fi
    else
        echo "Предупреждение: Группа $group_name не существует. Пользователь не был добавлен в нее."
    fi
}


# --- Параметры по умолчанию ---
DEFAULT_SHARE_PATH="/srv/shared"
CONFIG_FILE="/etc/samba/smb.conf"
WORKGROUP="WORKGROUP" # Можно изменить на имя вашей рабочей группы Windows/Samba

echo "=== Настройка Samba ==="

# --- 1. Проверка и установка Samba ---
DISTRO=$(detect_distro)
if ! command -v smbd &> /dev/null; then
    install_samba_packages "$DISTRO"
fi

# --- 2. Ввод пути к папке общего доступа ---
read -p "Введите путь к папке для общего доступа [по умолчанию: $DEFAULT_SHARE_PATH]: " SHARE_PATH
SHARE_PATH=${SHARE_PATH:-$DEFAULT_SHARE_PATH} # Если ввод пустой, использовать значение по умолчанию

# Создание папки для общего доступа
echo "Создание папки: $SHARE_PATH"
mkdir -p "$SHARE_PATH" || { echo "Ошибка: не удалось создать папку $SHARE_PATH." ; exit 1; }
chmod 2770 "$SHARE_PATH" || { echo "Ошибка: не удалось установить права на папку $SHARE_PATH." ; exit 1; }
chown nobody:nogroup "$SHARE_PATH" || { echo "Предупреждение: не удалось изменить владельца папки на nobody:nogroup. Используйте chown -R $SAMBA_USER:samba_users $SHARE_PATH для более строгих прав." ; }
echo "Папка $SHARE_PATH создана с правами 2770."

# --- 3. Выбор прав доступа ---
READ_ONLY=""
while [[ ! "$READ_ONLY" =~ ^(yes|no|y|n)$ ]]; do
    read -p "Общий доступ будет только для чтения? (yes/no) [по умолчанию: no]: " READ_ONLY
    READ_ONLY=${READ_ONLY:-no}
    READ_ONLY=$(echo "$READ_ONLY" | tr '[:upper:]' '[:lower:]') # Приводим к нижнему регистру
done

if [[ "$READ_ONLY" =~ ^(yes|y)$ ]]; then
  ACCESS="read only = yes"
else
  ACCESS="read only = no"
fi
echo "Права доступа установлены: $ACCESS"

# --- 4. Настройка пользователей Samba ---
SAMBA_USER=""
while [ -z "$SAMBA_USER" ]; do
    read -p "Введите имя пользователя для общего доступа Samba (не может быть пустым): " SAMBA_USER
done

# Проверка, существует ли системный пользователь
if id "$SAMBA_USER" &>/dev/null; then
  echo "Системный пользователь $SAMBA_USER уже существует."
else
  echo "Создание системного пользователя $SAMBA_USER..."
  useradd -m -s /sbin/nologin "$SAMBA_USER" || { echo "Ошибка: не удалось создать системного пользователя $SAMBA_USER." ; exit 1; }
  echo "Системный пользователь $SAMBA_USER создан."
fi

# Добавление пользователя в группу 'sambashare' или 'samba' (если есть) для лучшей совместимости
add_user_to_group "$SAMBA_USER" "sambashare"
add_user_to_group "$SAMBA_USER" "samba" # На некоторых системах может быть просто 'samba'

echo "Установка пароля для пользователя Samba..."
while true; do
    smbpasswd -a "$SAMBA_USER" || { echo "Ошибка установки пароля для Samba. Попробуйте еще раз." ; }
    if [ $? -eq 0 ]; then # Проверка успешности выполнения smbpasswd
        break
    fi
done
echo "Пароль для пользователя Samba $SAMBA_USER установлен."

# --- 5. Генерация конфигурационного файла smb.conf ---
echo "Создание/обновление конфигурационного файла $CONFIG_FILE"
# Делаем резервную копию существующего smb.conf
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak_$(date +%Y%m%d%H%M%S)"
    echo "Создана резервная копия: ${CONFIG_FILE}.bak_$(date +%Y%m%d%H%M%S)"
fi

# Пишем новый конфиг. Перезаписываем полностью, так как это установочный скрипт.
cat > "$CONFIG_FILE" <<EOF
[global]
   workgroup = $WORKGROUP
   server string = Samba Server %h
   netbios name = $(hostname)
   security = user
   map to guest = Bad User
   dns proxy = no
   # Прочие полезные настройки:
   unix charset = UTF-8
   dos charset = CP866
   client min protocol = SMB2
   server min protocol = SMB2

[$(basename "$SHARE_PATH")]
   path = $SHARE_PATH
   valid users = $SAMBA_USER
   $ACCESS
   browsable = yes
   guest ok = no
   create mask = 0664
   directory mask = 0775
   writable = yes # Этот параметр должен быть 'yes', если $ACCESS не 'read only = yes'
EOF

# Корректировка writable, чтобы не было конфликта с read only
if [[ "$ACCESS" =~ "read only = yes" ]]; then
    sed -i '/writable = yes/d' "$CONFIG_FILE" # Удалить writable=yes, если доступ только для чтения
else
    sed -i '/read only = yes/d' "$CONFIG_FILE" # Если не только для чтения, то убедиться, что read only = no установлен через $ACCESS
    # Проверяем, что writable=yes присутствует, если доступ для записи
    if ! grep -q "writable = yes" "$CONFIG_FILE"; then
        sed -i "/$ACCESS/a\   writable = yes" "$CONFIG_FILE" # Добавить writable = yes под ACCESS
    fi
fi


echo "Конфигурационный файл $CONFIG_FILE создан/обновлен."

# --- 6. Перезапуск службы Samba ---
echo "Перезапуск службы Samba..."
systemctl restart smbd nmbd || { echo "Ошибка: не удалось перезапустить службу Samba. Проверьте логи." ; exit 1; }
systemctl enable smbd nmbd || { echo "Ошибка: не удалось включить автозапуск службы Samba." ; }
echo "Служба Samba перезапущена и настроена на автозапуск."

# --- 7. Открытие портов файрвола (если ufw активен) ---
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    echo "Обнаружен UFW. Добавляем правила для Samba..."
    ufw allow samba || echo "Предупреждение: не удалось добавить правила UFW для Samba. Возможно, правила уже существуют."
    echo "Правила UFW для Samba добавлены."
elif command -v firewall-cmd &> /dev/null && systemctl is-active --quiet firewalld; then
    echo "Обнаружен Firewalld. Добавляем правила для Samba..."
    firewall-cmd --add-service=samba --permanent || echo "Предупреждение: не удалось добавить правила Firewalld для Samba."
    firewall-cmd --reload || echo "Предупреждение: не удалось перезагрузить Firewalld."
    echo "Правила Firewalld для Samba добавлены."
else
    echo "Предупреждение: UFW или Firewalld не обнаружены или не активны. Убедитесь, что порты Samba (139, 445/TCP) открыты в вашем файрволе."
fi


echo "=== Настройка Samba завершена успешно! ==="
echo "Теперь вы можете получить доступ к общей папке:"
echo "Путь к общей папке на данном компьютере: $SHARE_PATH"
echo "Имя пользователя Samba: $SAMBA_USER"
echo "Пароль: (тот, который вы установили ранее)"
echo ""
echo "Для доступа из Windows: \\\\$(hostname -I | awk '{print $1}')\\$(basename "$SHARE_PATH")"
echo "или \\\\$(hostname)\\$(basename "$SHARE_PATH")"
echo ""
echo "Для доступа из Linux/macOS: smb://$(hostname -I | awk '{print $1}')/$(basename "$SHARE_PATH")"
echo "или smb://$(hostname)/$(basename "$SHARE_PATH")"
echo ""
echo "Если возникли проблемы, проверьте логи Samba: journalctl -u smbd.service"
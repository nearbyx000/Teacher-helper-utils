#!/bin/bash

# Проверка прав
if [ "$(id -u)" -ne 0 ]; then
  echo "Пожалуйста, запустите скрипт с правами суперпользователя (sudo)."
  exit 1
fi

# Параметры
DEFAULT_SHARE_PATH="/srv/shared"
CONFIG_FILE="/etc/samba/smb.conf"
WORKGROUP="WORKGROUP"

echo "=== Настройка Samba ==="

# Ввод пути к папке общего доступа
read -p "Введите путь к папке для общего доступа [по умолчанию: $DEFAULT_SHARE_PATH]: " SHARE_PATH
SHARE_PATH=${SHARE_PATH:-$DEFAULT_SHARE_PATH}

# Создание папки для общего доступа
echo "Создание папки: $SHARE_PATH"
mkdir -p "$SHARE_PATH"
chmod 2770 "$SHARE_PATH"

# Выбор прав доступа
read -p "Общий доступ будет только для чтения? (yes/no) [по умолчанию: no]: " READ_ONLY
READ_ONLY=${READ_ONLY:-no}

if [[ "$READ_ONLY" =~ ^(yes|y)$ ]]; then
  ACCESS="read only = yes"
else
  ACCESS="read only = no"
fi

# Настройка пользователей
read -p "Введите имя пользователя для общего доступа: " SAMBA_USER
if id "$SAMBA_USER" &>/dev/null; then
  echo "Пользователь $SAMBA_USER уже существует."
else
  echo "Создание пользователя $SAMBA_USER..."
  useradd -m "$SAMBA_USER"
fi

echo "Установка пароля для пользователя Samba..."
smbpasswd -a "$SAMBA_USER"

# Генерация конфигурационного файла smb.conf
echo "Создание конфигурационного файла $CONFIG_FILE"
cat > "$CONFIG_FILE" <<EOF
[global]
   workgroup = $WORKGROUP
   server string = Samba Server
   netbios name = $(hostname)
   security = user
   map to guest = Bad User
   dns proxy = no

[$(basename $SHARE_PATH)]
   path = $SHARE_PATH
   valid users = $SAMBA_USER
   $ACCESS
   browsable = yes
EOF

# Перезапуск службы Samba
echo "Перезапуск службы Samba..."
systemctl enable smb nmb
systemctl restart smb nmb

# Вывод информации
echo "Samba успешно настроена."
echo "Папка для общего доступа: $SHARE_PATH"
echo "Файл конфигурации: $CONFIG_FILE"
echo "Доступ через Thunar: smb://$(hostname)/$(basename $SHARE_PATH)"

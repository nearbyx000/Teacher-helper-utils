#include <iostream>
#include <cstdlib>
#include <fstream>
#include <string>
#include <csignal>
#include <sys/types.h>
#include <unistd.h>
#include <fstream>
#include <nlohmann/json.hpp>

pid_t vncServerPid = -1;

// Проверяет, доступен ли указанный дисплей
bool isDisplayAvailable(int display) {
    std::string lockFile = "/tmp/.X" + std::to_string(display) + "-lock";
    std::ifstream file(lockFile);
    return !file.good(); // Если файла нет, дисплей доступен
}

// Находит первый доступный дисплей
int findAvailableDisplay() {
    for (int display = 1; display <= 10; ++display) {
        if (isDisplayAvailable(display)) {
            return display;
        }
    }
    return -1; // Если все дисплеи заняты
}
void loadConfig(const std::string& configPath, std::vector<std::pair<int, int>>& devices) {
    std::ifstream configFile(configPath);
    if (!configFile) {
        std::cerr << "Error: Unable to open config file.\n";
        exit(EXIT_FAILURE);
    }
    nlohmann::json config;
    configFile >> config;

    for (const auto& device : config["devices"]) {
        int display = device["display"];
        int port = device["port"];
        devices.emplace_back(display, port);
    }
}



// Функция для запуска VNC-сервера
void startVNCServer() {
    int display = findAvailableDisplay();
    if (display == -1) {
        std::cerr << "Error: No available displays found.\n";
        return;
    }

    const std::string command = "/usr/bin/Xvnc :" + std::to_string(display) +
                                " -geometry 1024x768 -rfbport 5901 -SecurityTypes None";
    std::cout << "Starting VNC server on display :" << display << ", port 5901..." << std::endl;

    vncServerPid = fork(); // Создаем дочерний процесс
    if (vncServerPid == 0) {
        // Дочерний процесс: запускаем VNC сервер
        execl("/bin/sh", "sh", "-c", command.c_str(), nullptr);
        std::cerr << "Error: Failed to start VNC server.\n";
        std::exit(1);
    } else if (vncServerPid < 0) {
        std::cerr << "Error: Unable to fork process for VNC server.\n";
    } else {
        std::cout << "VNC server started on display :" << display << " with PID: " << vncServerPid << std::endl;
    }
}

// Остановка VNC-сервера
void stopVNCServer() {
    if (vncServerPid > 0) {
        std::cout << "Stopping VNC server with PID: " << vncServerPid << "..." << std::endl;
        kill(vncServerPid, SIGTERM);
        vncServerPid = -1;
    } else {
        std::cerr << "VNC server is not running.\n";
    }
}

int main() {
    std::cout << "VNC Server Management Script\n";
    std::cout << "Commands: start, stop, exit\n";

    std::string command;
    while (true) {
        std::cout << "> ";
        std::cin >> command;

        if (command == "start") {
            startVNCServer();
        } else if (command == "stop") {
            stopVNCServer();
        } else if (command == "exit") {
            stopVNCServer();
            std::cout << "Exiting...\n";
            break;
        } else {
            std::cout << "Unknown command. Use 'start', 'stop', or 'exit'.\n";
        }
    }

    return 0;
}

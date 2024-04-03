import os
import sys
import re
import subprocess
from pythonping import ping
from tabulate import tabulate

class LestaClusterSelector:
    def __init__(self):
        self.servers = {
            "RU_C0 (Москва)": "login0.tanksblitz.ru",
            "RU_C1 (Москва)": "login1.tanksblitz.ru",
            "RU_C2 (Красноярск)": "login2.tanksblitz.ru",
            "RU_C3 (Екатеринбург)": "login3.tanksblitz.ru",
            "RU_C4 (Москва)": "login4.tanksblitz.ru",
            "RU_C5 (Москва)": "login5.tanksblitz.ru"
        }

        self.replacement_ip = "0.0.0.0"

        self.hosts_file_path_unix = '/etc/hosts'
        self.hosts_file_path_windows = r'C:\Windows\System32\drivers\etc\hosts'

    def update_hosts_file(self, selected_servers):
        if os.name == 'posix':  # Linux or macOS
            hosts_file_path = self.hosts_file_path_unix
        elif os.name == 'nt':  # Windows
            hosts_file_path = self.hosts_file_path_windows
        else:
            print("Unsupported OS")
            return

        if not os.path.exists(hosts_file_path):
            print(f"Файл {hosts_file_path} не найден.")
            return

        unselected_servers = [server for server in self.servers if server not in selected_servers]
        lines = self.read_hosts_file(hosts_file_path)
        self.write_hosts_file(hosts_file_path, lines, unselected_servers)

        print("Сервера успешно обновлены!")

    def read_hosts_file(self, file_path):
        with open(file_path, 'r') as file:
            return file.readlines()

    def write_hosts_file(self, file_path, lines, unselected_servers):
        with open(file_path, 'w') as file:
            for line in lines:
                if not any(server in line for server in self.servers.values()):
                    file.write(line)

            for server in unselected_servers:
                file.write(f"{self.replacement_ip} {self.servers[server]}\n")

    def show_menu(self):
        print()
        print("Выберите серверы для разблокировки:")
        for i, server in enumerate(self.servers.keys()):
            print(f"{i}. {server}")
        print("8. Разблокировать все сервера")
        print("9. Тестировать серверы по задержке")
        print()
        print("* - Введите номера серверов (через пробел), которые вы хотите разблокировать (1 2 3 4 5).")
        print("* - Или выберите действие, которые вы хотите выполнить (7/8/9).")
        print()
        
        choices = input("Выберите действие: ")
        print()
        selected_servers = self.get_selected_servers(choices)
        return selected_servers

    def get_selected_servers(self, choices):
        selected_servers = []
        for choice in choices.split():
            if choice.isdigit() and 0 <= int(choice) <= len(self.servers)-1:
                selected_servers.append(list(self.servers.keys())[int(choice)])
                self.update_hosts_file(selected_servers)
            elif choice == '8':
                selected_servers = list(self.servers.keys())
                self.update_hosts_file(selected_servers)
            elif choice == '9':
                results = self.ping_all_servers()
                print(tabulate(results, headers=["Сервер", "Статус"]))
                selected_servers.extend(server for server, status in results if status == "Недоступен")
        return selected_servers

    def ping_server(self, server_url):
        try:
            response = ping(server_url, count=5)
            if response.success():
                return {
                    "Среднее": response.rtt_avg_ms,
                    "Минимальное": response.rtt_min_ms,
                    "Максимальное": response.rtt_max_ms
                }
            else:
                return None
        except Exception as e:
            print(f"Ошибка при пинге сервера {server_url}: {e}")
            return None

    def ping_all_servers(self):
        results = []
        for server, url in self.servers.items():
            ping_result = self.ping_server(url)
            if ping_result is not None:
                results.append([server, ping_result])
            else:
                results.append([server, "Недоступен"])
        return results


def main():
    manager = LestaClusterSelector()
    while True:
        selected_servers = manager.show_menu()


def run_as_admin():
    os.execvp("sudo", ["sudo"] + [sys.executable] + sys.argv)


if __name__ == "__main__":
    if os.getuid() != 0:
        run_as_admin()
    else:
        main()

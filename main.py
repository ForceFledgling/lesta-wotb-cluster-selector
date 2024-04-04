import os
import sys
import re
import subprocess
from pythonping import ping
from tabulate import tabulate
from PyInquirer import prompt

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

    # def show_menu(self):
    #     print()
    #     print("Выберите серверы для разблокировки:")
    #     choices = [{
    #         'name': f"{server} - {url}",
    #         'value': server
    #     } for server, url in self.servers.items()]

    #     choices.append({'name': 'Разблокировать все сервера', 'value': 'all'})
    #     choices.append({'name': 'Тестировать серверы по задержке', 'value': 'ping'})

    #     questions = [
    #         {
    #             'type': 'checkbox',
    #             'message': 'Выберите действие:',
    #             'name': 'action',
    #             'choices': choices,
    #         }
    #     ]
    #     answers = prompt(questions)

    #     selected_servers = answers['action']
    #     if 'all' in selected_servers:
    #         selected_servers = list(self.servers.keys())
    #         self.update_hosts_file(selected_servers)
    #     elif 'ping' in selected_servers:
    #         results = self.ping_all_servers()
    #         print(tabulate(results, headers=["Сервер", "Статус"]))
    #         selected_servers.extend(server for server, status in results if status == "Недоступен")
    #     else:
    #         self.update_hosts_file(selected_servers)

    def show_menu(self):
        print()
        print("Выберите серверы для разблокировки:")
        choices = [{
            'name': f"{server} - {url}",
            'value': server
        } for server, url in self.servers.items()]

        choices.append({'name': 'Разблокировать все сервера', 'value': 'all'})
        choices.append({'name': 'Тестировать серверы по задержке', 'value': 'ping'})

        questions = [
            {
                'type': 'checkbox',
                'message': 'Выберите действие:',
                'name': 'action',
                'choices': choices,
            }
        ]
        answers = prompt(questions)

        selected_servers = answers['action']

        if 'ping' in selected_servers and len(selected_servers) > 1:
            print("Предупреждение: Выбор 'Тестировать серверы по задержке' несовместим с другими выборами.")
            return
        elif 'all' in selected_servers and len(selected_servers) > 1:
            print("Предупреждение: Выбор 'Разблокировать все сервера' несовместим с другими выборами.")
            return

        if 'all' in selected_servers:
            selected_servers = list(self.servers.keys())
            self.update_hosts_file(selected_servers)
        elif 'ping' in selected_servers:
            results = self.ping_all_servers()
            print(tabulate(results, headers=["Сервер", "Статус"]))
            selected_servers.extend(server for server, status in results if status == "Недоступен")
        else:
            self.update_hosts_file(selected_servers)

        if not selected_servers:
            return

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
        manager.show_menu()


def run_as_admin():
    os.execvp("sudo", ["sudo"] + [sys.executable] + sys.argv)


if __name__ == "__main__":
    if os.getuid() != 0:
        run_as_admin()
    else:
        main()

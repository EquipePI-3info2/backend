#!/usr/bin/env python3

import os
import socket


# Função para obter o IP do computador
def get_current_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f'Erro ao obter o IP: {e}')
        return None


# Função para atualizar o arquivo .env com o novo IP
def update_env_file(ip):
    try:
        if not os.path.isfile('.env'):
            with open('.env', 'w', encoding='utf-8') as new_file:
                new_file.write(f'MY_IP={ip}\n')
            return

        with open('.env', 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # ✅ Se MY_IP já está definido manualmente, não sobrescreve
        for line in lines:
            if line.startswith('MY_IP='):
                print(f'MY_IP já definido no .env, mantendo: {line.strip()}')
                return  # ← sai sem alterar nada

        # Só adiciona se não existia
        with open('.env', 'a', encoding='utf-8') as file:
            file.write(f'MY_IP={ip}\n')

        print(f'IP adicionado no .env: MY_IP={ip}')

    except Exception as e:
        print(f'Erro ao atualizar o arquivo .env: {e}')


# Função principal
def main():
    ip = get_current_ip()
    if ip:
        update_env_file(ip)


if __name__ == '__main__':
    main()

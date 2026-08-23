# AtendeMP Bonito

Aplicativo local para cadastro do público atendido pela Promotoria de Justiça de Bonito/PA, registro de atendimentos e controle de retornos.

## Recursos da primeira versão

- acesso por senha local;
- cadastro completo de pessoas, contatos, endereço e representante;
- resumo do caso e observações de vulnerabilidade/acessibilidade;
- histórico de atendimentos, providências, encaminhamentos e resultado;
- agenda de retornos com lembretes internos;
- pesquisa por nome, CPF, telefone ou protocolo;
- painel com quantitativos;
- trilha básica de auditoria;
- backup local do banco de dados.

## Executar

Requer Python 3.11 ou superior. O programa usa apenas a biblioteca padrão.

```bash
python app.py
```

No primeiro acesso, o sistema solicitará a criação da senha. O banco será criado em `dados/atendemp_bonito.db`.

## Gerar programa para Windows

### Baixar o executável pronto

Abra a aba **Actions** do repositório, escolha **Gerar programa para Windows**, acesse a execução mais recente concluída e baixe o artefato **AtendeMP-Bonito-Windows**. Extraia o ZIP e abra `AtendeMP-Bonito.exe`. Não é necessário instalar Python.

O Windows poderá exibir um aviso por se tratar de aplicativo próprio ainda não assinado digitalmente. Confirme a execução somente após verificar que o arquivo veio deste repositório.

### Gerar manualmente

```powershell
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name AtendeMP-Bonito app.py
```

O executável ficará na pasta `dist/`. Para manter os dados entre atualizações, preserve a pasta `dados` ao lado do executável.

## Segurança e proteção de dados

O acesso possui senha derivada com PBKDF2-HMAC-SHA256. O banco SQLite não é criptografado nesta versão. Use exclusivamente em computador institucional protegido, com perfil individual do Windows, bloqueio de tela, disco criptografado e backup em local autorizado. Não envie o arquivo do banco para o GitHub.

## Testes

```bash
python -m unittest discover -s tests -v
```

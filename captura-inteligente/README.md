# Captura Inteligente PJ

Ferramenta local para Windows que captura telas, executa OCR, gera PDF pesquisável e identifica dados úteis para procedimentos.

## Funções

- captura da tela visível;
- captura da janela ativa após contagem de 3 segundos;
- captura assistida com rolagem em várias páginas;
- importação de imagens;
- OCR local em português;
- identificação de procedimentos, ofícios, CPFs, datas, prazos, partes e legislação;
- PDF comum e PDF pesquisável;
- exportação do texto e da ficha em JSON.

## Limite da captura com rolagem

O programa registra várias telas enquanto o usuário rola manualmente a janela. O resultado é um PDF multipágina. Isso funciona de forma mais ampla do que tentar controlar automaticamente todos os programas do Windows.

## Dependências

1. Python 3.11 ou superior.
2. Pacotes de `requirements.txt`.
3. Tesseract OCR com o idioma português (`por`).

O Tesseract deve estar instalado em `C:\Program Files\Tesseract-OCR\tesseract.exe` ou disponível no PATH. A documentação oficial relaciona as opções de instalação para Windows: https://tesseract-ocr.github.io/tessdoc/Installation.html

## Executar pelo código

```powershell
py -m pip install -r requirements.txt
py app.py
```

## Proteção de dados

- As capturas e o OCR são processados localmente.
- O programa não envia conteúdo para a internet.
- Revise todos os dados extraídos antes de utilizá-los no SAJ.
- Salve resultados apenas em pasta institucional autorizada.
- Feche ou silencie notificações antes de capturar a tela.


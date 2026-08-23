# Captura de Tela PJ — versão simples

Ferramenta local para Windows com um único botão. Ao clicar, o programa se esconde, aguarda dois segundos, captura toda a tela e gera automaticamente PDF pesquisável e RTF editável.

## Funções

- captura de toda a tela após um clique;
- OCR local em português;
- identificação de procedimentos, ofícios, CPFs, datas, prazos, partes e legislação;
- PDF comum e PDF pesquisável;
- RTF editável com texto e informações identificadas;
- ficha técnica em JSON;
- imagem PNG original.

Os arquivos são salvos automaticamente em `Documentos\Capturas PJ`.

## Dependências

1. Python 3.11 ou superior.
2. Pacotes de `requirements.txt`.
3. Tesseract OCR com o idioma português (`por`).

O Tesseract deve estar instalado em `C:\Program Files\Tesseract-OCR\tesseract.exe` ou disponível no PATH. A documentação oficial relaciona as opções de instalação para Windows: https://tesseract-ocr.github.io/tessdoc/Installation.html

## Executar pelo código

```powershell
py -m pip install -r requirements.txt
py app_simples.py
```

## Proteção de dados

- As capturas e o OCR são processados localmente.
- O programa não envia conteúdo para a internet.
- Revise todos os dados extraídos antes de utilizá-los no SAJ.
- Salve resultados apenas em pasta institucional autorizada.
- Feche ou silencie notificações antes de capturar a tela.

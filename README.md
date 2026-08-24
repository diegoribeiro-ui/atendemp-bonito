# AtendeMP Bonito

Aplicativo local para cadastro do público atendido pela Promotoria de Justiça de Bonito/PA, registro de atendimentos e controle de retornos.

## Central IA — Projetos e Assistentes

O repositório também contém a **Central IA**, um painel local para organizar GPTs, Gems, notebooks do NotebookLM, projetos, prompts, arquivos, links, fluxos de trabalho e histórico de interações. A versão avançada inclui gerador orientado de assistentes, importação e exportação de fichas, Kanban, alertas de prazo, favoritos, avaliações, relatórios e bloqueio por senha local.

Abra `central-ia/Central-IA.html` diretamente no navegador. Os registros ficam salvos no próprio navegador e podem ser exportados pelo menu **Backup e dados**. Não publique dados institucionais ou pessoais no repositório.

## Ferramentas da PJ de Bonito

O arquivo `ferramentas-pj/Ferramentas-PJ-Bonito.html` reúne pequenas ferramentas guiadas para servidores e estagiários: tarefas internas, ficha de análise, controle de ofícios e prazos, matriz de conferência de respostas, cronologia, checklists por assunto, nomes padronizados de arquivos, e-mails institucionais, prompts, revisão de minutas e biblioteca de modelos e casos. Os conteúdos podem ser copiados, impressos, salvos no histórico e incluídos em backup local.

O módulo **Analisar arquivos** lê localmente PDFs com texto selecionável, DOCX, TXT, RTF e HTML; identifica dados, solicitações, respostas correspondentes, datas, prazos, alertas e cronologia; sugere nomes de arquivos e gera relatório e e-mail de pendências. Ele não utiliza IA nem OCR. A leitura de PDF e DOCX carrega bibliotecas JavaScript públicas pela internet, mas os documentos selecionados não são enviados por esse módulo.

Todas as abas operacionais também possuem um **Assistente automático desta aba**. O usuário pode colar texto ou selecionar um arquivo para obter inventário, conferência específica e preenchimento preliminar dos campos da tarefa, ficha, ofício, matriz, cronologia, checklist, nome de arquivo, e-mail, prompt, revisão ou biblioteca. As sugestões são baseadas em regras e sempre precisam ser conferidas.

O revisor de ofícios reconhece o padrão `OF. nº/ano–MP/PJB`, datas por extenso, destinatários múltiplos, assunto, referência administrativa e SAJ, pedido principal, subitens por letras, pontos de acompanhamento futuro, linguagem de cooperação, fecho e assinatura. Pedidos atuais e subitens são separados de meros referenciais de acompanhamento, evitando tratá-los automaticamente como cobranças imediatas. Respostas recebidas usam um checklist próprio.

O **Prompt Guiado** possui modo de reprodução orientada por modelo, com entradas separadas para o documento-modelo e os dados do novo caso. Ele detecta o tipo de peça, seções, marcadores, rótulos, conectores, extensão e padrão de citações; em ofícios, também distingue pedidos, subitens e acompanhamento futuro. O prompt gerado instrui a IA a aproveitar apenas a estrutura e o estilo do modelo, usando como fonte factual exclusiva os dados do novo caso. Há regras específicas para ofícios e denúncias criminais.

### Versão integrada das Ferramentas da PJ

A versão atual acrescenta um núcleo de **Casos e procedimentos**. Um caso ativo pode reunir ficha, tarefas, ofícios, prazos, textos, modelos e pendências. O sistema também inclui:

- rascunhos automáticos por aba e por caso;
- edição de casos, ofícios, itens da biblioteca e conteúdos do histórico;
- agenda única de ofícios e tarefas, exportável para Outlook (`.ics`) e CSV;
- acompanhamento de tarefas por responsável, prazo e situação;
- revisão especializada de ofício, resposta, despacho, denúncia, e-mail, manifestação e parecer;
- classificação reforçada de respostas e conferência de anexos mencionados;
- checklists personalizados;
- perfis estruturais reutilizáveis no Prompt Guiado;
- exportação de e-mail em `.eml`;
- backup validado, com opção de mesclar ou substituir;
- trilha local de auditoria e espelho dos dados em IndexedDB;
- pesquisa conjunta em casos, tarefas, ofícios, biblioteca e histórico.

O assistente de documentos também produz um **Inventário técnico ampliado**, com identidade documental, pessoas para conferência, órgãos, procedimentos, datas, prazos, valores, contatos, identificadores, normas, seções, anexos, providências e palavras recorrentes. Há três saídas copiáveis: inventário completo, resumo extrativo com indicação das fontes e ficha preliminar para conferência e cadastro no SAJ. O resumo utiliza somente frases extraídas do próprio documento; dados sem confirmação permanecem sinalizados ou em branco.

Os dados continuam locais e não são criptografados. O espelho em IndexedDB melhora a resistência do armazenamento, mas não substitui o backup periódico nem o uso de perfil individual protegido no Windows.

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

Abra a aba **Actions** do repositório, escolha **Gerar programa para Windows**, acesse a execução mais recente concluída e baixe o artefato **AtendeMP-Bonito-Windows**. Extraia o ZIP inteiro, abra a pasta `AtendeMP-Bonito` e execute `INICIAR.bat`. Não mova apenas o `.exe`: os demais arquivos da pasta são necessários. Não é necessário instalar Python.

O Windows poderá exibir um aviso por se tratar de aplicativo próprio ainda não assinado digitalmente. Confirme a execução somente após verificar que o arquivo veio deste repositório.

### Gerar manualmente

```powershell
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --onedir --windowed --name AtendeMP-Bonito app.py
```

O executável ficará na pasta `dist/`. Para manter os dados entre atualizações, preserve a pasta `dados` ao lado do executável.

## Segurança e proteção de dados

O acesso possui senha derivada com PBKDF2-HMAC-SHA256. O banco SQLite não é criptografado nesta versão. Use exclusivamente em computador institucional protegido, com perfil individual do Windows, bloqueio de tela, disco criptografado e backup em local autorizado. Não envie o arquivo do banco para o GitHub.

## Testes

```bash
python -m unittest discover -s tests -v
```

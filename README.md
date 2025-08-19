# Robo Labirinto

Projeto educacional para popularização do pensamento computacional, com demonstração lúdica e interativa de algoritmos em Python.

## Funcionalidades

- Geração automática de labirintos em diferentes dificuldades
- Controle do robô por teclado ou por detecção de cor via webcam
- Interface gráfica com Pygame e integração com OpenCV

## Como funciona a geração de labirintos

- Geração procedural por backtracking (DFS)
- Estrutura em grade (linhas x colunas) de células (classe `Celula`)
- Cada célula inicia com todas as paredes fechadas: cima, baixo, esquerda, direita = True; e `visitada = False`

### Busca de vizinhos
- Retorna vizinhos válidos (cima, baixo, esquerda, direita) que ainda não foram visitados, respeitando os limites da grade
- Cada vizinho é acompanhado da direção relativa (“cima”, “baixo”, “esquerda”, “direita”)

### Remoção de paredes
- Abrir passagem entre duas células significa:
  - `atual.paredes[direcao] = False`
  - `vizinho.paredes[oposto(direcao)] = False` (sincroniza ambas as células)

### Algoritmo (DFS com backtracking)
1. Inicia na célula (0, 0), marca como visitada e usa uma pilha para backtracking
2. Coleta vizinhos não visitados da célula atual
3. Se houver vizinhos:
   - Escolhe um vizinho aleatório
   - Remove a parede entre atual e vizinho
   - Empilha a célula atual
   - Marca o vizinho como visitado e torna-o a célula atual
   - Atualiza a “última célula” com a célula atual
4. Se não houver vizinhos, mas a pilha não está vazia:
   - Faz backtracking: desempilha e retorna à célula anterior
5. Se a pilha estiver vazia:
   - Finaliza (todas as células foram visitadas)

Propriedade: gera um “labirinto perfeito” (existe exatamente um caminho simples entre quaisquer duas células, sem ciclos).

### Ajuste do objetivo final
- Ao terminar, percorre as células visitadas e seleciona a de maior distância Manhattan a partir de (0,0), desde que seja pelo menos 8
- Se nenhuma atingir 8, retorna a célula inicial
- Essa célula é usada como objetivo

## Como executar

1. Instale as dependências:
   ```bash
   pip install pygame opencv-python numpy
   ```
2. Execute o programa:
   ```bash
   python robo.py
   ```

## Controles

- Setas: girar ou mover o robô
- Espaço: avançar
- Enter: executar sequência de comandos (modo comando)
- Webcam: detecta cores (vermelho, azul, verde) para controlar o robô

## Créditos

Projeto Computação para Todos - FURG - 2025
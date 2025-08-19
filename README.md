# Robo Labirinto

Projeto educacional para popularização do pensamento computacional, com demonstração lúdica e interativa de algoritmos em Python

## Funcionalidades

- Geração automática de labirintos em diferentes dificuldades
- Controle do robô por teclado ou por detecção de cor via webcam
- Interface gráfica com pygame e integração com OpenCV

## Como funciona a geração de labirintos

- Geração procedural com backtracking
- Utiliza uma grid de células. Cada célula (classe Celula) começa com todas as paredes fechadas: cima, baixo, esquerda, direita = True, e visitada = False
- O labirinto é uma grade 2D de Celula, com dimensões linhas x colunas
- Buscar vizinhos: retorna uma lista de vizinhos acessíveis (cima, baixo, esquerda, direita) que ainda não foram visitados, respeitando os limites da grade
- Cada vizinho vem acompanhado da direção relativa (“cima”, “baixo”, “esquerda”, “direita”)
- Removendo parede: abre espaço entre duas células: atual e a vizinha opostas
- Backtracking: Inicia o caminho na célula (0,0) e marca como visitada. Mantém uma pilha para backtracking.
   Loop:
      1. Coleta vizinhos não visitados da célula atual.
      2. Se houver vizinhos:
         - Escolhe um vizinho aleatório.
         - Remove a parede entre atual e vizinho.
         - Empilha a célula atual.
         - Marca o vizinho como visitado e passa a ser a célula atual.
         - Atualiza a última célula com a célula atual.
      3. Se não houver vizinhos, mas a pilha não está vazia:
         - Faz backtracking: desempilha e volta para a célula anterior.
      4. se não houver vizinhos e a pilha está vazia:
         - Terminou a geração (todas as células foram visitadas).
   Propriedade: isso gera um "labirinto perfeito" (uma única rota simples entre quaisquer duas células, sem ciclos).

- Ajuste do objetivo final:
   Ao terminar, chama uma função que percorre todas as células visitadas e seleciona aa que tem maior distância Manhattan a partir de (0,0), desde que seja pelo menos 8. se nenhuma atingir 8, retorna a célula inicial. Essa última célula encontrada funciona como o objetivo.

## Como executar

1. Instale as dependências:
   ```
   pip install pygame opencv-python numpy
   ```
2. Execute o programa:
   ```
   python robo.py
   ```

## Controles

- **Setas**: Girar ou mover o robô
- **Espaço**: Avançar
- **Enter**: Executar sequência de comandos (modo comando)
- **Webcam**: Detecta cores (vermelho, azul, verde) para controlar o robô

## Créditos

Projeto Computação para Todos - FURG - 2025
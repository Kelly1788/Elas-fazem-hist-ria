# Tudo que aparece na janela e responde ao mouse: desenhar botões, mostrar o retrato,
# detectar clique, trocar de tela (título, investigação, hipótese, revelação). É a classe Jogo do protótipo,
# e é a única que usa o pygame para desenhar.

# O que aparece na tela e o que acontece quando clico?
#PYGAME 


"""
ELAS FIZERAM HISTÓRIA - jogo de investigação histórica (pygame)

O aluno investiga documentos, imagens e depoimentos de 4 dossiês, marca as pistas,
formula uma hipótese e descobre a mulher que a história tentou apagar.

POO: FonteHistorica (abstrata) -> Documento, Depoimento, Imagem (polimorfismo);
     Caso tem Fontes, Caderno e Protagonista (composição); Caderno encapsula a pontuação.

Executar:  pip install pygame  &&  python elas_fizeram_historia.py
Os textos das fontes são adaptados/parafraseados para fins didáticos:
revise com o(a) professor(a) de História antes de usar em sala.
"""
import math
import random
import sys
from abc import ABC, abstractmethod

import pygame

LARGURA, ALTURA = 1100, 680
FUNDO = (24, 18, 38)
PAINEL = (46, 38, 66)
PAINEL2 = (58, 48, 82)
TEXTO = (236, 232, 242)
SUAVE = (165, 155, 190)
OURO = (244, 196, 80)
ROSA = (236, 102, 162)
VERDE = (96, 200, 130)
VERMELHO = (228, 92, 100)
ROXO = (150, 110, 220)


def quebrar_texto(texto, fonte, largura):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if fonte.size(teste)[0] <= largura:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


# ============================================================ MODELO
class Trecho:
    def __init__(self, texto, relevante, explicacao):
        self.texto = texto
        self.relevante = relevante
        self.explicacao = explicacao


class FonteHistorica(ABC):
    def __init__(self, titulo, autor, ano, trechos):
        self.titulo, self.autor, self.ano, self.trechos = titulo, autor, ano, trechos

    @property
    @abstractmethod
    def tipo(self): ...

    @property
    @abstractmethod
    def cor(self): ...

    @abstractmethod
    def pergunta_critica(self): ...

    @abstractmethod
    def desenhar_ilustracao(self, tela, rect): ...


class Documento(FonteHistorica):
    tipo = "Documento"
    cor = (214, 184, 120)

    def pergunta_critica(self):
        return "Quem produziu este documento e com que objetivo?"

    def desenhar_ilustracao(self, tela, rect):
        pygame.draw.rect(tela, (226, 206, 160), rect, border_radius=6)
        for i in range(5):
            y = rect.y + 14 + i * 14
            pygame.draw.line(tela, (150, 125, 80), (rect.x + 20, y), (rect.right - 20 - (i % 2) * 60, y), 2)


class Depoimento(FonteHistorica):
    tipo = "Depoimento"
    cor = (130, 200, 180)

    def pergunta_critica(self):
        return "A testemunha estava presente? Tinha algum interesse ou preconceito?"

    def desenhar_ilustracao(self, tela, rect):
        pygame.draw.rect(tela, (62, 100, 96), rect, border_radius=6)
        aspas = pygame.font.SysFont("dejavusans,arial", 80, bold=True).render("\u201c", True, (200, 236, 226))
        tela.blit(aspas, (rect.x + 20, rect.y - 10))


class Imagem(FonteHistorica):
    tipo = "Imagem"
    cor = (200, 150, 220)

    def pergunta_critica(self):
        return "Quando foi feita? Quem a produziu e para quem?"

    def desenhar_ilustracao(self, tela, rect):
        pygame.draw.rect(tela, (90, 70, 120), rect, border_radius=6)
        moldura = rect.inflate(-16, -12)
        pygame.draw.rect(tela, (215, 190, 120), moldura, 3)
        tela.set_clip(moldura)
        cx, cy = moldura.centerx, moldura.centery
        pygame.draw.circle(tela, (60, 45, 85), (cx, cy - 10), 16)
        pygame.draw.ellipse(tela, (60, 45, 85), (cx - 30, cy + 8, 60, 44))
        tela.set_clip(None)


class Pista:
    def __init__(self, trecho, fonte):
        self.trecho, self.fonte = trecho, fonte


class Caderno:
    def __init__(self):
        self._pistas = []

    def alternar(self, trecho, fonte):
        for p in self._pistas:
            if p.trecho is trecho:
                self._pistas.remove(p)
                return
        self._pistas.append(Pista(trecho, fonte))

    def contem(self, trecho):
        return any(p.trecho is trecho for p in self._pistas)

    @property
    def pistas(self):
        return list(self._pistas)

    def certas(self):
        return sum(p.trecho.relevante for p in self._pistas)

    def pontuacao(self):
        return sum(10 if p.trecho.relevante else -5 for p in self._pistas)


class Protagonista:
    def __init__(self, nome, epoca, feito, frase):
        self.nome, self.epoca, self.feito, self.frase = nome, epoca, feito, frase


class Caso:
    def __init__(self, codinome, pergunta, enunciado, fontes, hipoteses, correta, conclusao, protagonista):
        self.codinome, self.pergunta, self.enunciado = codinome, pergunta, enunciado
        self.fontes, self.hipoteses, self.correta = fontes, hipoteses, correta
        self.conclusao, self.protagonista = conclusao, protagonista
        self.caderno = Caderno()
        self.erradas = set()
        self.resolvido = False

    def total_relevantes(self):
        return sum(t.relevante for f in self.fontes for t in f.trechos)

    def pontos_maximos(self):
        return self.total_relevantes() * 10 + 40

    def responder(self, indice):
        if indice == self.correta:
            self.resolvido = True
            return True
        self.erradas.add(indice)
        return False

    def pontos(self):
        if not self.resolvido:
            return 0
        bonus = max(40 - 20 * len(self.erradas), 0)
        return max(0, self.caderno.pontuacao() + bonus)


def T(texto, rel, expl):
    return Trecho(texto, rel, expl)


def criar_casos():
    caso1 = Caso(
        "O Soldado Medeiros",
        "Quem era, de fato, o \"soldado Medeiros\"?",
        "Bahia, 1822. Registros militares elogiam a coragem de um soldado chamado Medeiros. "
        "Mas há algo estranho nos documentos... Quem era essa pessoa?",
        [
            Documento("Registro do Batalhão dos Periquitos (adaptado)", "Escrivão militar", "1822", [
                T("O nome \"Medeiros\" consta no registro, mas há indícios de que não era a identidade verdadeira do combatente.",
                  True, "Uma identidade falsa sugere que alguém escondia algo: pista central."),
                T("Mulheres não podiam se alistar no exército; para entrar, seria preciso esconder quem era.",
                  True, "O contexto da época explica por que o disfarce era necessário."),
                T("O documento foi escrito com tinta escura em papel grosso.",
                  False, "Detalhe material sem relação com a pergunta.")]),
            Depoimento("Diário de Maria Graham (parafraseado)", "Maria Graham, escritora inglesa", "1823", [
                T("A escritora conta ter conhecido uma jovem soldada, que entrou na guerra vestida de homem e se destacou em combate.",
                  True, "Uma testemunha da época confirma a hipótese do disfarce."),
                T("Ela era estrangeira e escrevia para leitores europeus, o que pode ter influenciado o tom do relato.",
                  True, "Boa crítica de fonte: quem escreve, para quem e de onde."),
                T("A escritora reclama do calor durante a viagem de navio.",
                  False, "Curioso, mas não ajuda a resolver o caso.")]),
            Imagem("Retrato de Maria Quitéria (Domenico Failutti)", "Domenico Failutti, pintor", "1920", [
                T("A pintura mostra uma mulher em uniforme militar, segurando um fuzil.",
                  True, "A imagem reforça que houve uma mulher combatente."),
                T("O quadro foi pintado quase cem anos depois, então mostra como a memória nacional a imaginou.",
                  True, "Fontes produzidas muito depois exigem cautela."),
                T("A moldura do quadro é dourada.",
                  False, "Elemento decorativo sem valor para o caso.")]),
        ],
        ["Um veterano português que mudou de lado durante a guerra.",
         "Uma jovem baiana que se disfarçou de homem para lutar pela Independência.",
         "Um personagem inventado para levantar o moral das tropas."],
        1,
        "O \"soldado Medeiros\" era Maria Quitéria, jovem baiana que se alistou disfarçada e foi "
        "condecorada por Dom Pedro I em 1823.",
        Protagonista("Maria Quitéria de Jesus", "Bahia, 1792 \u2013 1853",
                     "Cortou o cabelo, vestiu a farda e lutou nas batalhas pela Independência da Bahia.",
                     "Cortou o cabelo, vestiu a farda e enfrentou um império. A história demorou a escrever o nome dela."),
    )

    caso2 = Caso(
        "A Primeira Eleitora",
        "O voto feminino foi um presente ou uma conquista?",
        "Brasil, anos 1920. Uma professora do interior do Rio Grande do Norte pede para entrar na lista de "
        "eleitores, algo considerado impensável. De onde veio o direito de voto das mulheres?",
        [
            Documento("Requerimento de alistamento eleitoral (adaptado)", "Professora Celina Guimarães Viana", "1927", [
                T("Uma professora de Mossoró (RN) pede para ser incluída entre os eleitores e o juiz aceita, com base em uma lei estadual.",
                  True, "Prova que uma mulher agiu por conta própria para exigir o direito."),
                T("Mesmo com o alistamento aceito, os votos das potiguares foram depois anulados por uma comissão do Senado.",
                  True, "Mostra a resistência institucional que elas enfrentaram."),
                T("O requerimento foi escrito à mão, em folha pautada.",
                  False, "Detalhe material, sem relação com a pergunta.")]),
            Depoimento("Manifesto das sufragistas (parafraseado)", "Bertha Lutz e a Federação Brasileira pelo Progresso Feminino", "1922-1932", [
                T("Bertha Lutz fundou em 1922 uma federação para lutar pelo voto e pela educação das mulheres.",
                  True, "Mostra organização coletiva por trás da conquista."),
                T("As sufragistas fizeram campanhas, abaixo-assinados e pressionaram parlamentares por mais de dez anos.",
                  True, "Uma luta longa, e não um presente."),
                T("Bertha Lutz também era zoóloga e estudava anfíbios.",
                  False, "Curioso, mas não responde ao caso.")]),
            Imagem("Charge de revista da época (adaptada)", "Cartunista anônimo", "anos 1920", [
                T("A charge ridiculariza mulheres que pedem o voto, mostrando-as abandonando a casa e os filhos.",
                  True, "Revela o preconceito e a resistência que elas enfrentavam."),
                T("Charges eram feitas para o grande público, então mostram o que muita gente pensava na época.",
                  True, "Ótima análise: a imagem é fonte sobre mentalidades."),
                T("A charge foi desenhada em traços rápidos, em preto e branco.",
                  False, "Aspecto técnico sem ajuda para o caso.")]),
        ],
        ["Foi um presente dos governantes, sem pressão de ninguém.",
         "Foi fruto de anos de mobilização de mulheres que exigiram o direito de votar.",
         "Nunca houve resistência: todos concordavam desde o início."],
        1,
        "O voto feminino nacional veio com o Código Eleitoral de 1932, depois de anos de luta de sufragistas "
        "como Bertha Lutz e de gestos pioneiros como o de Celina, a primeira eleitora do país (1927).",
        Protagonista("Celina Guimarães Viana e Bertha Lutz", "Rio Grande do Norte e Rio de Janeiro, séc. XX",
                     "Celina foi a primeira eleitora do Brasil (1927); Bertha liderou a campanha nacional pelo voto.",
                     "Ninguém deu o voto às mulheres. Elas o conquistaram, uma assinatura de cada vez."),
    )

    caso3 = Caso(
        "A Foto 51",
        "Quem produziu a prova que revelou a forma do DNA?",
        "Inglaterra, 1953. A estrutura do DNA é anunciada ao mundo. Nos bastidores, uma imagem de raios X foi "
        "decisiva. Quem a produziu, e quem recebeu o crédito?",
        [
            Documento("Artigo na revista Nature (adaptado)", "James Watson e Francis Crick", "1953", [
                T("O artigo apresenta o modelo da dupla hélice e só menciona de forma vaga \"resultados não publicados\" de outros pesquisadores.",
                  True, "O crédito aos outros cientistas foi bem discreto."),
                T("Na mesma edição saíram artigos de Rosalind Franklin e de Maurice Wilkins com dados de raios X que sustentavam o modelo.",
                  True, "As evidências experimentais vinham do laboratório dela."),
                T("O artigo tem pouco mais de uma página.",
                  False, "O tamanho do texto não ajuda a resolver o caso.")]),
            Depoimento("Relato de colegas do laboratório (parafraseado)", "Colegas do King's College, Londres", "anos 1950", [
                T("Colegas contam que Rosalind Franklin era uma das maiores especialistas do mundo em cristalografia de raios X.",
                  True, "Mostra a competência dela, não uma coadjuvante."),
                T("Sem que ela soubesse, um colega mostrou a Watson a imagem que ela e seu aluno haviam produzido: a Foto 51.",
                  True, "O uso sem consentimento é a pista central."),
                T("Franklin gostava de fazer caminhadas nas montanhas.",
                  False, "Curiosidade pessoal, irrelevante para o caso.")]),
            Imagem("Foto 51: difração de raios X do DNA", "Rosalind Franklin e Raymond Gosling", "1952", [
                T("A imagem mostra um padrão em forma de X, típico de uma estrutura em hélice.",
                  True, "A própria imagem apontava para a dupla hélice."),
                T("A foto foi feita por Franklin e seu aluno de doutorado, e não pelos autores do modelo.",
                  True, "Estabelece a autoria da evidência."),
                T("A imagem é em preto e branco.",
                  False, "Característica técnica sem valor para a resposta.")]),
        ],
        ["Watson e Crick descobriram tudo sozinhos, sem usar dados de ninguém.",
         "Os dados de uma cristalógrafa foram essenciais e usados sem que ela soubesse.",
         "A cientista copiou o trabalho de Watson e Crick."],
        1,
        "Rosalind Franklin produziu evidências decisivas. Ela morreu em 1958; o Nobel de 1962 foi para "
        "Watson, Crick e Wilkins (o prêmio não é concedido após a morte).",
        Protagonista("Rosalind Franklin", "Inglaterra, 1920 \u2013 1958",
                     "Cristalógrafa cujos dados de raios X, incluindo a Foto 51, foram essenciais para revelar o DNA.",
                     "A imagem que mostrou a forma da vida foi feita por ela. O reconhecimento chegou tarde demais."),
    )

    caso4 = Caso(
        "A Rainha do Quariterê",
        "Quem comandava o Quilombo do Quariterê?",
        "Mato Grosso, século XVIII. Relatórios coloniais falam de um quilombo que resistiu por anos às "
        "expedições. Quem estava por trás dessa resistência?",
        [
            Documento("Registro colonial de Vila Bela (adaptado)", "Autoridades coloniais", "1770", [
                T("Os administradores descrevem o quilombo como bem organizado, com plantações, tecelagem e forja de ferramentas.",
                  True, "Mostra que havia planejamento e liderança, não desordem."),
                T("O documento cita uma \"rainha\" que comandava o quilombo até ser capturada.",
                  True, "Indica uma liderança feminina reconhecida até pelos inimigos."),
                T("O relatório detalha os gastos com a viagem das tropas.",
                  False, "Informação burocrática sem relação com a pergunta.")]),
            Depoimento("Tradição oral do Mato Grosso (parafraseada)", "Comunidades quilombolas", "transmitida por gerações", [
                T("A tradição conta que Tereza de Benguela governava com um conselho e organizava a defesa do quilombo.",
                  True, "A memória oral preservou o que os documentos ignoraram."),
                T("Por ser memória oral, o relato pode mudar com o tempo e deve ser cruzado com documentos.",
                  True, "Boa crítica de fonte: comparar versões."),
                T("Os moradores dizem que a região tem muitos rios.",
                  False, "Detalhe geográfico que não resolve o caso.")]),
            Imagem("Cartaz do Dia de Tereza de Benguela (adaptado)", "Movimentos de mulheres negras", "século XXI", [
                T("O cartaz homenageia Tereza de Benguela e lembra o 25 de julho, Dia Nacional de Tereza de Benguela e da Mulher Negra.",
                  True, "A memória dela foi resgatada como símbolo de resistência."),
                T("Por ser uma fonte moderna, mostra como Tereza é lembrada hoje, não o que ocorreu no século XVIII.",
                  True, "Distinguir fonte da época de homenagem posterior."),
                T("O cartaz usa as cores roxo e amarelo.",
                  False, "Escolha estética sem relação com a pergunta.")]),
        ],
        ["Um capitão-do-mato que mudou de lado.",
         "Uma liderança feminina que organizou política, economia e defesa.",
         "Ninguém: era só um grupo desorganizado de fugitivos."],
        1,
        "Tereza de Benguela liderou o Quilombo do Quariterê, que combinava agricultura, produção de "
        "ferramentas e defesa organizada. Foi capturada em 1770 e sua memória vive na luta das mulheres negras.",
        Protagonista("Tereza de Benguela", "Mato Grosso, século XVIII",
                     "Liderou o Quilombo do Quariterê, que resistiu por anos ao domínio colonial.",
                     "Onde o Império viu fuga, ela construiu um reino."),
    )
    return [caso1, caso2, caso3, caso4]


FRASE_FINAL_1 = "Nunca faltaram mulheres na história. Faltaram páginas."
FRASE_FINAL_2 = "Agora você sabe onde procurar, e o que contar."


# ============================================================ JOGO
class Jogo:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Elas Fizeram História")
        self.clock = pygame.time.Clock()
        f = "dejavusans,arial"
        self.f_gigante = pygame.font.SysFont(f, 56, bold=True)
        self.f_nome = pygame.font.SysFont(f, 42, bold=True)
        self.f_frase = pygame.font.SysFont(f, 27, italic=True)
        self.f_titulo = pygame.font.SysFont(f, 26, bold=True)
        self.f_normal = pygame.font.SysFont(f, 16)
        self.f_pequena = pygame.font.SysFont(f, 14)
        self.f_italica = pygame.font.SysFont(f, 15, italic=True)
        random.seed(7)
        self.estrelas = [(random.randint(0, LARGURA), random.randint(0, ALTURA),
                          random.randint(1, 2), random.random() * 6) for _ in range(70)]
        self.reiniciar()

    def reiniciar(self):
        self.casos = criar_casos()
        self.caso_atual = 0
        self.fonte_atual = 0
        self.mudar_estado("titulo")

    def mudar_estado(self, estado):
        self.estado = estado
        self.t = 0
        self.areas = []

    @property
    def caso(self):
        return self.casos[self.caso_atual]

    def todos_resolvidos(self):
        return all(c.resolvido for c in self.casos)

    def pontos_totais(self):
        return sum(c.pontos() for c in self.casos)

    def pontos_maximos(self):
        return sum(c.pontos_maximos() for c in self.casos)

    # ---------- cliques
    def tratar_clique(self, pos):
        for rect, acao, dado in self.areas:
            if not rect.collidepoint(pos):
                continue
            if acao == "iniciar" or acao == "hub":
                self.mudar_estado("hub")
            elif acao == "abrir_caso":
                self.caso_atual, self.fonte_atual = dado, 0
                self.mudar_estado("revelacao" if self.caso.resolvido else "investigacao")
            elif acao == "fonte":
                self.fonte_atual = dado
            elif acao == "trecho":
                self.caso.caderno.alternar(dado, self.caso.fontes[self.fonte_atual])
            elif acao == "concluir":
                self.mudar_estado("conclusao")
            elif acao == "voltar_fontes":
                self.mudar_estado("investigacao")
            elif acao == "hipotese":
                if self.caso.responder(dado):
                    self.mudar_estado("revelacao")
            elif acao == "continuar":
                self.mudar_estado("epilogo" if self.todos_resolvidos() else "hub")
            elif acao == "epilogo":
                self.mudar_estado("epilogo")
            elif acao == "reiniciar":
                self.reiniciar()
            return

    # ---------- helpers de desenho
    def texto(self, txt, fonte, cor, x, y, largura=None, max_linhas=None):
        linhas = quebrar_texto(txt, fonte, largura) if largura else [txt]
        if max_linhas and len(linhas) > max_linhas:
            linhas = linhas[:max_linhas]
            linhas[-1] = linhas[-1][:-3] + "..."
        for ln in linhas:
            self.tela.blit(fonte.render(ln, True, cor), (x, y))
            y += fonte.get_linesize() + 2
        return y

    def texto_centro(self, txt, fonte, cor, cx, y, largura=None):
        linhas = quebrar_texto(txt, fonte, largura) if largura else [txt]
        for ln in linhas:
            img = fonte.render(ln, True, cor)
            self.tela.blit(img, (cx - img.get_width() // 2, y))
            y += fonte.get_linesize() + 4
        return y

    def texto_maquina(self, txt, fonte, cor, cx, y, largura, inicio):
        """Efeito de máquina de escrever: 1 caractere por quadro."""
        restante = max(0, self.t - inicio)
        for ln in quebrar_texto(txt, fonte, largura):
            x = cx - fonte.size(ln)[0] // 2
            self.tela.blit(fonte.render(ln[:restante], True, cor), (x, y))
            restante -= len(ln) + 1
            y += fonte.get_linesize() + 6
        return y

    def botao(self, rect, rotulo, cor, acao, dado=None, ativo=True):
        if not ativo:
            cor = (78, 72, 96)
        elif rect.collidepoint(pygame.mouse.get_pos()):
            cor = tuple(min(255, c + 25) for c in cor)
        pygame.draw.rect(self.tela, cor, rect, border_radius=10)
        img = self.f_normal.render(rotulo, True, (24, 18, 38))
        self.tela.blit(img, img.get_rect(center=rect.center))
        if ativo:
            self.areas.append((rect, acao, dado))

    def estrelas_fundo(self):
        for x, y, r, fase in self.estrelas:
            b = 120 + int(100 * math.sin(self.t * 0.05 + fase))
            pygame.draw.circle(self.tela, (b, b, min(255, b + 40)), (x, y), r)

    # ---------- telas
    def tela_titulo(self):
        self.estrelas_fundo()
        cx = LARGURA // 2
        self.texto_centro("ELAS FIZERAM", self.f_gigante, OURO, cx, 130)
        self.texto_centro("HISTÓRIA", self.f_gigante, ROSA, cx, 195)
        self.texto_centro("Um jogo de investigação histórica", self.f_normal, SUAVE, cx, 275)
        self.texto_maquina("Nem todas as heroínas ficaram nas páginas. Cabe a você encontrá-las.",
                           self.f_frase, TEXTO, cx, 340, 900, 15)
        self.botao(pygame.Rect(cx - 150, 480, 300, 56), "Iniciar investigação", OURO, "iniciar")

    def tela_hub(self):
        self.texto("Dossiês abertos", self.f_titulo, OURO, 60, 30)
        self.texto("Escolha um caso. Cada um esconde uma mulher que a história tentou esquecer.",
                   self.f_normal, SUAVE, 60, 72)
        mouse = pygame.mouse.get_pos()
        for i, caso in enumerate(self.casos):
            r = pygame.Rect(60 + (i % 2) * 510, 120 + (i // 2) * 200, 480, 180)
            pygame.draw.rect(self.tela, PAINEL, r, border_radius=12)
            borda = VERDE if caso.resolvido else (OURO if r.collidepoint(mouse) else PAINEL2)
            pygame.draw.rect(self.tela, borda, r, 2, border_radius=12)
            self.texto(f"CASO {i + 1}", self.f_pequena, SUAVE, r.x + 20, r.y + 14)
            self.texto(caso.codinome, self.f_titulo, OURO, r.x + 20, r.y + 34)
            self.texto(caso.enunciado, self.f_pequena, TEXTO, r.x + 20, r.y + 74, 440, 3)
            if caso.resolvido:
                self.texto("\u2713 Resolvido: " + caso.protagonista.nome, self.f_pequena, VERDE,
                           r.x + 20, r.bottom - 32, 440, 1)
            else:
                self.texto("Em aberto \u2022 protagonista: ???", self.f_pequena, SUAVE, r.x + 20, r.bottom - 32)
            self.areas.append((r, "abrir_caso", i))
        self.texto(f"Pontuação: {self.pontos_totais()} / {self.pontos_maximos()}", self.f_normal, TEXTO, 60, 560)
        pronto = self.todos_resolvidos()
        self.botao(pygame.Rect(LARGURA - 320, 540, 260, 50), "Ver epílogo", ROSA, "epilogo", ativo=pronto)
        if not pronto:
            self.texto("Resolva os 4 casos para liberar o epílogo.", self.f_pequena, SUAVE, LARGURA - 320, 600)

    def tela_investigacao(self):
        caso = self.caso
        self.texto(f"Caso {self.caso_atual + 1}: {caso.codinome}", self.f_titulo, OURO, 20, 14)
        self.texto(caso.enunciado, self.f_pequena, SUAVE, 20, 50, LARGURA - 40, 2)

        y = 100
        self.texto("FONTES", self.f_pequena, SUAVE, 20, y)
        y += 24
        for i, fonte in enumerate(caso.fontes):
            r = pygame.Rect(20, y, 210, 70)
            sel = i == self.fonte_atual
            pygame.draw.rect(self.tela, fonte.cor if sel else PAINEL, r, border_radius=8)
            cor_t = (24, 18, 38) if sel else TEXTO
            self.texto(fonte.tipo, self.f_pequena, cor_t, r.x + 10, r.y + 8)
            self.texto(fonte.titulo, self.f_pequena, cor_t, r.x + 10, r.y + 26, 190, 2)
            self.areas.append((r, "fonte", i))
            y += 80
        self.botao(pygame.Rect(20, y + 10, 210, 44), "\u2190 Casos", ROXO, "hub")

        fonte = caso.fontes[self.fonte_atual]
        centro = pygame.Rect(250, 100, 520, 560)
        pygame.draw.rect(self.tela, PAINEL, centro, border_radius=10)
        self.texto(fonte.titulo, self.f_normal, fonte.cor, centro.x + 16, centro.y + 12, 490)
        self.texto(f"{fonte.autor}  \u2022  {fonte.ano}", self.f_pequena, SUAVE, centro.x + 16, centro.y + 34, 490, 1)
        fonte.desenhar_ilustracao(self.tela, pygame.Rect(centro.x + 16, centro.y + 62, 488, 90))
        y = self.texto("Pergunta crítica: " + fonte.pergunta_critica(), self.f_italica, OURO,
                       centro.x + 16, centro.y + 162, 490) + 6
        self.texto("Clique nos trechos que considera pistas:", self.f_pequena, SUAVE, centro.x + 16, y)
        y += 24
        for trecho in fonte.trechos:
            linhas = quebrar_texto(trecho.texto, self.f_normal, 470)
            h = len(linhas) * (self.f_normal.get_linesize() + 2) + 14
            r = pygame.Rect(centro.x + 16, y, 488, h)
            marcado = caso.caderno.contem(trecho)
            pygame.draw.rect(self.tela, PAINEL2 if marcado else (54, 45, 76), r, border_radius=8)
            pygame.draw.rect(self.tela, OURO if marcado else (78, 68, 104), r, 2, border_radius=8)
            self.texto(trecho.texto, self.f_normal, TEXTO, r.x + 10, r.y + 7, 470)
            self.areas.append((r, "trecho", trecho))
            y += h + 10

        cad = pygame.Rect(790, 100, 290, 470)
        pygame.draw.rect(self.tela, PAINEL, cad, border_radius=10)
        self.texto(f"CADERNO DE PISTAS ({len(caso.caderno.pistas)})", self.f_pequena, OURO, cad.x + 14, cad.y + 12)
        y = cad.y + 40
        for p in caso.caderno.pistas:
            if y > cad.bottom - 50:
                break
            y = self.texto("\u2022 " + p.trecho.texto, self.f_pequena, TEXTO, cad.x + 14, y, 262, 3) + 6
        pode = len(caso.caderno.pistas) >= 3
        self.botao(pygame.Rect(790, 590, 290, 50), "Formular hipótese", VERDE, "concluir", ativo=pode)
        if not pode:
            self.texto("Colete ao menos 3 pistas.", self.f_pequena, SUAVE, 790, 646)

    def tela_conclusao(self):
        caso = self.caso
        self.texto("Hora de concluir!", self.f_titulo, OURO, 60, 40)
        self.texto(caso.pergunta, self.f_normal, TEXTO, 60, 85, LARGURA - 120)
        y = 140
        for i, hip in enumerate(caso.hipoteses):
            r = pygame.Rect(60, y, LARGURA - 120, 80)
            errada = i in caso.erradas
            pygame.draw.rect(self.tela, (40, 32, 52) if errada else PAINEL, r, border_radius=10)
            sobre = r.collidepoint(pygame.mouse.get_pos()) and not errada
            pygame.draw.rect(self.tela, VERMELHO if errada else (OURO if sobre else PAINEL2), r, 2, border_radius=10)
            self.texto(f"{chr(65 + i)}) {hip}", self.f_normal, SUAVE if errada else TEXTO, r.x + 20, r.y + 28, r.w - 40)
            if errada:
                self.texto("Não se sustenta nas fontes", self.f_pequena, VERMELHO, r.right - 220, r.y + 6)
            else:
                self.areas.append((r, "hipotese", i))
            y += 100
        if caso.erradas:
            self.texto("Revise as pistas e tente outra hipótese. Cada erro reduz o bônus do caso.",
                       self.f_pequena, OURO, 60, 450)
        self.botao(pygame.Rect(60, 500, 240, 46), "Voltar às fontes", ROXO, "voltar_fontes")

    def tela_revelacao(self):
        caso, prot = self.caso, self.caso.protagonista
        cx = LARGURA // 2
        self.estrelas_fundo()
        self.texto_centro("CASO ENCERRADO", self.f_pequena, SUAVE, cx, 30)
        self.texto_centro("A protagonista era...", self.f_normal, SUAVE, cx, 58)
        nome = prot.nome if self.t > 30 else "? ? ?"
        self.texto_centro(nome, self.f_nome, ROSA, cx, 92, 1000)
        if self.t > 30:
            self.texto_centro(prot.epoca, self.f_pequena, SUAVE, cx, 152)
            self.texto_centro(prot.feito, self.f_normal, TEXTO, cx, 182, 800)
        caixa = pygame.Rect(90, 250, LARGURA - 180, 190)
        pygame.draw.rect(self.tela, PAINEL, caixa, border_radius=14)
        pygame.draw.rect(self.tela, OURO, caixa, 2, border_radius=14)
        self.texto_maquina(prot.frase, self.f_frase, OURO, cx, caixa.y + 40, caixa.w - 80, 60)
        if self.t > 150:
            self.texto_centro(caso.conclusao, self.f_pequena, SUAVE, cx, 470, 900)
            self.texto_centro(
                f"Pistas certas: {caso.caderno.certas()}/{caso.total_relevantes()}   |   "
                f"Erros de hipótese: {len(caso.erradas)}   |   Pontos do caso: {caso.pontos()}",
                self.f_normal, TEXTO, cx, 540)
            ultimo = self.todos_resolvidos()
            self.botao(pygame.Rect(cx - 140, 590, 280, 50),
                       "Ir para o epílogo" if ultimo else "Próximo dossiê", OURO, "continuar")

    def tela_epilogo(self):
        cx = LARGURA // 2
        self.estrelas_fundo()
        self.texto_centro("EPÍLOGO", self.f_titulo, OURO, cx, 26)
        for i, caso in enumerate(self.casos):
            r = pygame.Rect(40 + i * 264, 80, 250, 110)
            pygame.draw.rect(self.tela, PAINEL, r, border_radius=10)
            pygame.draw.rect(self.tela, ROSA, r, 2, border_radius=10)
            self.texto_centro(caso.protagonista.nome, self.f_normal, TEXTO, r.centerx, r.y + 14, 226)
            self.texto_centro(caso.protagonista.epoca, self.f_pequena, SUAVE, r.centerx, r.y + 78, 226)
        y = self.texto_maquina(FRASE_FINAL_1, self.f_nome if False else self.f_titulo, OURO, cx, 250, 950, 20)
        self.texto_maquina(FRASE_FINAL_2, self.f_frase, ROSA, cx, y + 20, 950, 20 + len(FRASE_FINAL_1) + 15)
        if self.t > 160:
            perc = self.pontos_totais() / self.pontos_maximos()
            patente = ("Aprendiz de Arquivo" if perc < 0.4 else "Investigador(a)" if perc < 0.7
                       else "Detetive da História" if perc < 0.9 else "Guardião(ã) da Memória")
            self.texto_centro(f"Pontuação final: {self.pontos_totais()} / {self.pontos_maximos()}   \u2022   Patente: {patente}",
                              self.f_normal, TEXTO, cx, 470)
            self.texto_centro("Conte essas histórias. Elas merecem ser lembradas.", self.f_italica, SUAVE, cx, 510)
            self.botao(pygame.Rect(cx - 120, 570, 240, 48), "Jogar de novo", OURO, "reiniciar")
            self.botao(pygame.Rect(cx + 140, 570, 200, 48), "Dossiês", ROXO, "hub")

    # ---------- laço principal
    def executar(self):
        telas = {"titulo": self.tela_titulo, "hub": self.tela_hub, "investigacao": self.tela_investigacao,
                 "conclusao": self.tela_conclusao, "revelacao": self.tela_revelacao, "epilogo": self.tela_epilogo}
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.tratar_clique(ev.pos)
            self.tela.fill(FUNDO)
            self.areas = []
            telas[self.estado]()
            pygame.display.flip()
            self.t += 1
            self.clock.tick(30)


if __name__ == "__main__":
    Jogo().executar()
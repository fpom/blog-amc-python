import hashlib, random, string, tempfile, pathlib, subprocess, shutil

random.seed(12345)

WORDS = set(word for word in (l.strip() for l in open("words.txt"))
            if 3 <= len(word) <= 8
            and word[-1] != "s")

class RainbowTable (object) :
    def __init__ (self, tlen=10, clen=3) :
        self.tlen = tlen
        self.clen = clen
        self.salt = "".join(random.sample(string.printable, 6))
        self.words = random.sample(list(sorted(WORDS)), tlen * (clen + 1))
        self.spare = random.sample(list(sorted(WORDS - set(self.words))), tlen)
        self.chains = {}
        self.reduce = {}
        for i in range(tlen) :
            ch = self._chain(self.words[i::tlen])
            self.chains[ch[0]] = ch
        self.table = [(start, chain[-1]) for start, chain in self.chains.items()]
        self._t = {b: a for a, b in self.table}
    def h (self, w) :
        return hashlib.sha256((w + self.salt).encode("utf-8")).hexdigest()[-6:].upper()
    def r (self, h) :
        return self.reduce[h]
    def _chain (self, words) :
        assert len(words) == self.clen + 1, words
        last = words[-1]
        chain = []
        for i, w in enumerate(words) :
            chain.append(w)
            if w != last :
                h = self.h(w)
                chain.append(h)
                assert h not in self.reduce
                self.reduce[h] = words[i+1]
        return chain
    def table_tex (self, out) :
        out.write(r"\begin{tabular}{|c>{\columncolor{yellow!15!white}}%"
                  r"s>{\columncolor{green!15!white}}c|}" % ("c" * (4*self.clen)))
        out.write("\n\\hline &")
        out.write(" && ".join(fr"$\color{{gray}}W_{{{i}}}$"
                              fr"&& $\color{{gray}}E_{{{i}}}$" for i in range(self.clen))
                  + f" && $\color{{gray}}W_{{{self.clen}}}$ \\bigstrut[tb]\\\\\n\\hline")
        for n, chain in enumerate(self.chains.values()) :
            out.write(fr"{{\relsize{{-1}}\color{{gray}}({n})}} & ")
            for i, elt in enumerate(chain) :
                if i :
                    out.write(" & ")
                    if i % 2 :
                        out.write(r"\to{h\bigstrut[t]} & ")
                    else :
                        out.write(r"\to{r_{%s}\bigstrut[t]} & " % (i//2 - 1))
                if i % 2 :
                    out.write(r"\hash{%s}" % elt)
                else :
                    out.write(r"\text{%s}" % elt)
            out.write(r"\bigstrut\\" + "\n")
        out.write(r"\hline\end{tabular}" + "\n")
    def table_pdf (self, path) :
        with tempfile.TemporaryDirectory() as tmp :
            texpath = pathlib.Path(tmp) / "rt.tex"
            with open(texpath, "w") as tex :
                tex.write("\n".join([
                    r"\documentclass{standalone}",
                    r"\usepackage{bigstrut}",
                    r"\usepackage{relsize}",
                    r"\usepackage{xcolor}",
                    r"\usepackage{colortbl}",
                    r"\def\text #1{{\color{blue!40!black}{\texttt{#1}}}}",
                    r"\def\hash #1{{\colorbox{red!10!white}{\color{red!30!black}"
                    r"\texttt{#1}}}}",
                    r"\def\to #1{\ensuremath{\stackrel{#1}{\longrightarrow}}}",
                    r"\begin{document}"]) + "\n")
                self.table_tex(tex)
                tex.write(r"\end{document}" + "\n")
            subprocess.check_output(["latexmk", "-pdf", f"-outdir={tmp}", texpath],
                                    stderr=subprocess.STDOUT)
            shutil.move(texpath.with_suffix(".pdf"), path)
    def macros (self, out) :
        for line, chain in enumerate(self.chains.values()) :
            for row, txt in enumerate(chain[0::2]) :
                out.write(fr"\expandafter\def\csname W{line},{row}\endcsname"
                          fr"{{\word{{{txt}}}}}" "\n")
            for row, txt in enumerate(chain[1::2]) :
                out.write(fr"\expandafter\def\csname H{line},{row}\endcsname"
                          fr"{{\hash{{{txt}}}}}" "\n")
        for i, w in enumerate(self.spare) :
            h = self.h(w)
            assert h not in self.reduce
            out.write(fr"\expandafter\def\csname W,{i}\endcsname"
                      fr"{{\word{{{w}}}}}" "\n")
            out.write(fr"\expandafter\def\csname H,{i}\endcsname"
                      fr"{{\hash{{{h}}}}}" "\n")

if __name__ == "__main__" :
    import tqdm
    inc = pathlib.Path("../inc")
    inc.mkdir(exist_ok=True)
    for num in tqdm.tqdm(range(1, 11)) :
        r = RainbowTable()
        r.table_pdf(inc / f"C{num}.pdf")
        with open(inc / f"C{num}.tex", "w") as out :
            r.macros(out)

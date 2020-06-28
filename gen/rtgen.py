import hashlib, random, string, tempfile, pathlib, subprocess, shutil

# don't forget to intialise the random seed with a constant
random.seed(12345)

# a set of words of lenth 2 to 8, without the plural forms to avoid confusion
WORDS = set(word for word in (l.strip() for l in open("words.txt"))
            if 3 <= len(word) <= 8
            and word[-1] != "s")

class RainbowTable (object) :
    # mocked rainbow table, like the example in Wikipedia
    def __init__ (self, tlen=10, clen=3) :
        # tlen = number of rows
        # clen = number of reduce fonctions (so #rows = 2 * clen + 1)
        self.tlen = tlen
        self.clen = clen
        # a salt for hashing so two students won't have the same hash function
        self.salt = "".join(random.sample(string.printable, 6))
        # the words in the table
        # note how the set is sorted to a list to avoid non deterministic executions
        self.words = random.sample(list(sorted(WORDS)), tlen * (clen + 1))
        # a set of spare words not in the table
        self.spare = random.sample(list(sorted(WORDS - set(self.words))), tlen)
        # the chains stored as {'first word' : [content of the chain]}
        self.chains = {}
        # the reduction function, there is only one even if we pretend the contrary
        self.reduce = {}
        # generate the cgains
        for i in range(tlen) :
            ch = self._chain(self.words[i::tlen])
            self.chains[ch[0]] = ch
    def h (self, w) :
        # hash function: salted SHA256 keeping only the last 6 chars of the hexdigest
        return hashlib.sha256((w + self.salt).encode("utf-8")).hexdigest()[-6:].upper()
    def r (self, h) :
        # reduce fonction, statically defined
        return self.reduce[h]
    def _chain (self, words) :
        # generate a chain including the provided words
        assert len(words) == self.clen + 1, words
        last = words[-1]
        chain = []
        for i, w in enumerate(words) :
            # insert a word in the chain
            chain.append(w)
            if w != last :
                # if this is not the last one, insert a hash
                h = self.h(w)
                chain.append(h)
                # detect collision that would cause inconsistencies
                assert h not in self.reduce
                # assign reduction function so it yields the next word
                self.reduce[h] = words[i+1]
        return chain
    def table_tex (self, out) :
        # save the table as a LaTeX tabular
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
        # generate a PDF using latex
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
        # save the cells of the table
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
    # generate as many tables as needed
    import tqdm
    inc = pathlib.Path("../inc")
    inc.mkdir(exist_ok=True)
    for num in tqdm.tqdm(range(1, 11)) :
        r = RainbowTable()
        r.table_pdf(inc / f"C{num}.pdf")
        with open(inc / f"C{num}.tex", "w") as out :
            r.macros(out)

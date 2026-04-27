# -*- coding: utf-8 -*-
#
#  TOPPERS .tf template engine (Python port) -- parser
#
#  C++ macro_processor.cpp:174-447 の Boost.Spirit 文法を逐写した
#  再帰下降パーサ．Segment ストリーム (PLAIN/DIR の 2 種) を入力に取り，
#  Document AST を返す．
#

from typing import List, Optional, Tuple

from tf_ast import (
    Document, PlainText, EvalExpr, Assign,
    IfStmt, ForeachStmt, JoinEachStmt, WhileStmt, JoinWhileStmt,
    FunctionDef, ErrorDir, WarningDir, FileDir,
    IntLit, StrLit, Ident, IndexedIdent, UnaryOp, BinOp, Call, ListExpr,
)
from tf_lexer import Segment, Tok, tokenize_directive

# ディレクティブのキーワード一覧
_BLOCK_OPENERS = (
    "IF", "FOREACH", "JOINEACH", "WHILE", "JOINWHILE",
    "FUNCTION", "ERROR", "WARNING",
)
_BLOCK_STOPPERS = ("END", "ELIF", "ELSEIF", "ELSE")
_ATOMIC_DIRECTIVES = ("FILE",)


# ============================================================
# Token stream (式評価用)
# ============================================================

class TokenStream:
    def __init__(self, tokens: List[Tok]):
        self.toks = tokens
        self.pos = 0

    def peek(self, k: int = 0) -> Optional[Tok]:
        idx = self.pos + k
        return self.toks[idx] if idx < len(self.toks) else None

    def eof(self) -> bool:
        return self.pos >= len(self.toks)

    def advance(self) -> Tok:
        t = self.toks[self.pos]
        self.pos += 1
        return t

    def match(self, kind: str, value=None) -> Optional[Tok]:
        t = self.peek()
        if t is None or t.kind != kind:
            return None
        if value is not None and t.value != value:
            return None
        self.pos += 1
        return t

    def match_op(self, *ops) -> Optional[Tok]:
        t = self.peek()
        if t is None or t.kind != 'OP':
            return None
        if t.value in ops:
            self.pos += 1
            return t
        return None

    def expect(self, kind: str, value=None) -> Tok:
        t = self.match(kind, value)
        if t is None:
            got = self.peek()
            raise SyntaxError(
                f"expected {kind}{'(' + repr(value) + ')' if value else ''}"
                f", got {got!r}"
            )
        return t

    def expect_op(self, *ops) -> Tok:
        t = self.match_op(*ops)
        if t is None:
            got = self.peek()
            raise SyntaxError(f"expected one of {ops}, got {got!r}")
        return t


# ============================================================
# 式パーサ (TokenStream 上で動作する)
# ============================================================

def parse_expression(ts: TokenStream):
    return _logical_or(ts)


def _logical_or(ts):
    left = _logical_and(ts)
    while ts.match_op('||'):
        right = _logical_and(ts)
        left = BinOp('||', left, right)
    return left


def _logical_and(ts):
    left = _or_expr(ts)
    while ts.match_op('&&'):
        right = _or_expr(ts)
        left = BinOp('&&', left, right)
    return left


def _or_expr(ts):
    left = _xor_expr(ts)
    while ts.match_op('|'):
        right = _xor_expr(ts)
        left = BinOp('|', left, right)
    return left


def _xor_expr(ts):
    left = _and_expr(ts)
    while ts.match_op('^'):
        right = _and_expr(ts)
        left = BinOp('^', left, right)
    return left


def _and_expr(ts):
    left = _equality(ts)
    while ts.match_op('&'):
        right = _equality(ts)
        left = BinOp('&', left, right)
    return left


def _equality(ts):
    left = _relational(ts)
    while True:
        op = ts.match_op('==', '!=')
        if not op:
            break
        right = _relational(ts)
        left = BinOp(op.value, left, right)
    return left


def _relational(ts):
    left = _shift(ts)
    while True:
        op = ts.match_op('<=', '>=', '<', '>')
        if not op:
            break
        right = _shift(ts)
        left = BinOp(op.value, left, right)
    return left


def _shift(ts):
    left = _additive(ts)
    while True:
        op = ts.match_op('<<', '>>')
        if not op:
            break
        right = _additive(ts)
        left = BinOp(op.value, left, right)
    return left


def _additive(ts):
    left = _multiplicative(ts)
    while True:
        op = ts.match_op('+', '-')
        if not op:
            break
        right = _multiplicative(ts)
        left = BinOp(op.value, left, right)
    return left


def _multiplicative(ts):
    left = _unary(ts)
    while True:
        op = ts.match_op('*', '/', '%')
        if not op:
            break
        right = _unary(ts)
        left = BinOp(op.value, left, right)
    return left


def _unary(ts):
    # *chset<>("-+~!@") >> postfix_expr  ─ 0 個以上の単項
    ops = []
    while True:
        op = ts.match_op('-', '+', '~', '!', '@')
        if not op:
            break
        ops.append(op.value)
    node = _postfix(ts)
    for op in reversed(ops):
        node = UnaryOp(op, node)
    return node


def _postfix(ts):
    # identifier '(' (expr % ',')* ')'  |  primary
    t = ts.peek()
    if t and t.kind == 'IDENT' and ts.peek(1) and ts.peek(1).kind == 'OP' \
            and ts.peek(1).value == '(':
        name_tok = ts.advance()
        ts.expect_op('(')
        args = []
        if not (ts.peek() and ts.peek().kind == 'OP' and ts.peek().value == ')'):
            args.append(parse_expression(ts))
            while ts.match_op(','):
                args.append(parse_expression(ts))
        ts.expect_op(')')
        return Call(name_tok.value, args, line=name_tok.line)
    return _primary(ts)


def _primary(ts):
    # lvalue | ordered_list | constant | string_literal | '(' expr ')'
    t = ts.peek()
    if t is None:
        raise SyntaxError("unexpected end of expression")
    if t.kind == 'OP' and t.value == '(':
        ts.advance()
        e = parse_expression(ts)
        ts.expect_op(')')
        return e
    if t.kind == 'OP' and t.value == '{':
        return _ordered_list(ts)
    if t.kind == 'NUM':
        ts.advance()
        return IntLit(t.value, str(t.value), line=t.line)
    if t.kind == 'STR':
        ts.advance()
        return StrLit(t.value, line=t.line)
    if t.kind == 'IDENT':
        return _lvalue(ts)
    raise SyntaxError(f"unexpected token in primary: {t!r}")


def _lvalue(ts):
    t = ts.expect('IDENT')
    if ts.peek() and ts.peek().kind == 'OP' and ts.peek().value == '[':
        ts.advance()
        idx = parse_expression(ts)
        ts.expect_op(']')
        return IndexedIdent(t.value, idx, line=t.line)
    return Ident(t.value, line=t.line)


def _ordered_list(ts):
    # '{' ((ordered_sequence | ordered_item) (';' ...)*)? '}'
    open_t = ts.expect_op('{')
    line = open_t.line
    if ts.match_op('}'):
        return ListExpr(items=[], line=line)
    items = []
    sequence = False
    seq_start = seq_second = seq_end = None
    # 1 グループ目をパース
    first_item, info = _ordered_group(ts)
    if info is not None:
        sequence = True
        seq_start, seq_second, seq_end = info
    items.extend(first_item)
    while ts.match_op(';'):
        next_item, info = _ordered_group(ts)
        if info is not None:
            # 2 つ目以降のシーケンス指定は表現上別グループだが現状未対応
            sequence = True
            seq_start, seq_second, seq_end = info
        items.extend(next_item)
    ts.expect_op('}')
    return ListExpr(
        items=items, sequence=sequence,
        start=seq_start, second=seq_second, end=seq_end, line=line,
    )


def _ordered_group(ts):
    """ordered_sequence または ordered_item 1 つ分を読む．

    戻り値: (items, sequence_info or None)．
    - sequence_info が None なら ordered_item: items はカンマ区切り全要素
    - sequence_info が tuple なら ordered_sequence: items は 3 要素 [start, second, end]
    """
    # ordered_sequence は constant ',' constant ',' '...' ',' constant
    # 先読み: NUM ',' NUM ',' '...' を満たすか試す
    save = ts.pos
    if ts.peek() and ts.peek().kind == 'NUM':
        try:
            n1 = ts.advance()
            op1 = ts.match_op(',')
            n2 = None
            op_dots = None
            n3 = None
            if op1 and ts.peek() and ts.peek().kind == 'NUM':
                n2 = ts.advance()
                if ts.match_op(',') and ts.match_op('...') and ts.match_op(','):
                    if ts.peek() and ts.peek().kind == 'NUM':
                        n3 = ts.advance()
                        return (
                            [IntLit(n1.value, str(n1.value), line=n1.line),
                             IntLit(n2.value, str(n2.value), line=n2.line),
                             IntLit(n3.value, str(n3.value), line=n3.line)],
                            (
                                IntLit(n1.value, str(n1.value), line=n1.line),
                                IntLit(n2.value, str(n2.value), line=n2.line),
                                IntLit(n3.value, str(n3.value), line=n3.line),
                            ),
                        )
        except SyntaxError:
            pass
        ts.pos = save
    # 通常の ordered_item
    items = [parse_expression(ts)]
    while True:
        # 次が ',' なら追加，ただし `, ...` のシーケンス用カンマと衝突しないよう
        # (実装上ここまで来た時点でシーケンスは既に試されているので問題なし)
        if not (ts.peek() and ts.peek().kind == 'OP' and ts.peek().value == ','):
            break
        # 次の次が '}' か ';' か '...' なら break
        nxt = ts.peek(1)
        if nxt and nxt.kind == 'OP' and nxt.value == '...':
            break
        ts.advance()  # ','
        items.append(parse_expression(ts))
    return (items, None)


# ============================================================
# Directive content parser
# ============================================================

def _parse_assignment_or_eval(tokens: List[Tok], line: int):
    """`$ ... $` の中身が assignment_expr または eval-expression のどちらかを判定する．

    Boost.Spirit grammar: ('$' >> ( assignment_expr | expression ) >> '$') - "$END$" - "$ELSE$"
    Python 側ではまず lvalue を試して `=` が続けば代入，さもなくば式評価．
    """
    ts = TokenStream(tokens)
    # 先読み: IDENT [ '[' expr ']' ]? '='  なら assignment_expr
    # それ以外は eval expression
    save_pos = ts.pos
    is_assign = False
    if ts.peek() and ts.peek().kind == 'IDENT':
        # IDENT を仮消費
        ts.advance()
        if ts.peek() and ts.peek().kind == 'OP' and ts.peek().value == '[':
            # IDENT [ expr ] = ...
            try:
                ts.advance()
                # expression を消費するが副作用がない範囲で軽く確認したい．
                # ここでは単純に '=' が登場するまで対応する '[' '(' '{' のネストを
                # 数えて見つける方式に倒す．
                bracket_depth = 1
                paren_depth = 0
                brace_depth = 0
                while not ts.eof():
                    tk = ts.peek()
                    if tk.kind == 'OP':
                        if tk.value == '[':
                            bracket_depth += 1
                        elif tk.value == ']':
                            bracket_depth -= 1
                            if bracket_depth == 0:
                                ts.advance()
                                break
                        elif tk.value == '(':
                            paren_depth += 1
                        elif tk.value == ')':
                            paren_depth -= 1
                        elif tk.value == '{':
                            brace_depth += 1
                        elif tk.value == '}':
                            brace_depth -= 1
                    ts.advance()
                if ts.peek() and ts.peek().kind == 'OP' and ts.peek().value == '=':
                    is_assign = True
            except SyntaxError:
                pass
        elif ts.peek() and ts.peek().kind == 'OP' and ts.peek().value == '=':
            is_assign = True
    ts.pos = save_pos
    if is_assign:
        # IDENT [ '[' expr ']' ]? '=' expression
        name_tok = ts.expect('IDENT')
        idx_expr = None
        if ts.match_op('['):
            idx_expr = parse_expression(ts)
            ts.expect_op(']')
        ts.expect_op('=')
        rhs = parse_expression(ts)
        if not ts.eof():
            extra = ts.peek()
            raise SyntaxError(f"unexpected token after assignment: {extra!r}")
        return Assign(name_tok.value, idx_expr, rhs, line=line)
    # 式評価
    expr = parse_expression(ts)
    if not ts.eof():
        extra = ts.peek()
        raise SyntaxError(f"unexpected token after expression: {extra!r}")
    return EvalExpr(expr, line=line)


# ============================================================
# Segment-level parser
# ============================================================

class Parser:
    def __init__(self, segments: List[Segment]):
        self.segs = segments
        self.pos = 0

    def parse(self) -> Document:
        doc, hit = self._parse_top(stoppers=('EOF',))
        return doc

    # ----- 内部ヘルパ -----

    def _peek(self) -> Optional[Segment]:
        return self.segs[self.pos] if self.pos < len(self.segs) else None

    def _advance(self) -> Segment:
        s = self.segs[self.pos]
        self.pos += 1
        return s

    def _dir_head(self, seg: Segment) -> Tuple[Optional[str], List[Tok]]:
        """DIR セグメントの先頭キーワードと残りのトークンを返す．"""
        toks = tokenize_directive(seg.text, base_line=seg.line)
        if not toks:
            return (None, toks)
        first = toks[0]
        if first.kind == 'IDENT' and first.value in (
            *_BLOCK_OPENERS, *_BLOCK_STOPPERS, *_ATOMIC_DIRECTIVES,
        ):
            return (first.value, toks)
        return (None, toks)

    # ----- 主処理 -----

    def _parse_top(self, stoppers: Tuple[str, ...]) -> Tuple[Document, str]:
        """stoppers で指定したキーワードのいずれかが出現するまで Document を蓄積．

        stoppers には 'EOF' を含めると入力末尾でも停止．
        戻り値: (Document, ヒットした stopper キーワード)．
        ヒットした stopper セグメントは **未消費** のまま残す．

        ※ Plain text の whitespace 取扱いは tf_eval.exec_stmt 側で C++
        macro_processor::plain (line 1682-1709) に従って行う:
          - 先頭文字が whitespace なら 1 文字スキップ
          - 中の \r / \n は出力しない
        パーサ側はトリミングしない (= 元の text を素通しする)．
        """
        children = []
        while True:
            seg = self._peek()
            if seg is None:
                if 'EOF' in stoppers:
                    return Document(children), 'EOF'
                raise SyntaxError("unexpected end of input")
            if seg.kind == 'PLAIN':
                self._advance()
                if seg.text:
                    children.append(PlainText(seg.text, seg.line))
                continue
            # DIR
            head, toks = self._dir_head(seg)
            if head in stoppers:
                return Document(children), head
            stmt = self._parse_directive(seg, head, toks)
            children.append(stmt)
        # unreachable
        raise SyntaxError("internal: parse loop exited unexpectedly")

    def _parse_directive(self, seg: Segment, head: Optional[str],
                          toks: List[Tok]):
        line = seg.line
        if head is None:
            # 通常の式 / 代入
            self._advance()
            return _parse_assignment_or_eval(toks, line)
        # キーワードディレクティブ
        self._advance()
        if head == 'IF':
            return self._parse_if(line, toks[1:])
        if head == 'FOREACH':
            return self._parse_foreach(line, toks[1:])
        if head == 'JOINEACH':
            return self._parse_joineach(line, toks[1:])
        if head == 'WHILE':
            return self._parse_while(line, toks[1:])
        if head == 'JOINWHILE':
            return self._parse_joinwhile(line, toks[1:])
        if head == 'FUNCTION':
            return self._parse_function(line, toks[1:])
        if head == 'ERROR':
            return self._parse_error_warning(line, toks[1:], is_error=True)
        if head == 'WARNING':
            return self._parse_error_warning(line, toks[1:], is_error=False)
        if head == 'FILE':
            return self._parse_file(line, toks[1:])
        raise SyntaxError(f"unknown directive: ${head}$")

    # ----- 個別ディレクティブ -----

    def _parse_if(self, line: int, rest: List[Tok]) -> IfStmt:
        # 最初の cond は rest にある
        cond = self._parse_full_expr(rest)
        body, hit = self._parse_top(stoppers=('ELIF', 'ELSEIF', 'ELSE', 'END'))
        cases = [(cond, body)]
        else_body = None
        while hit in ('ELIF', 'ELSEIF'):
            stop_seg = self._advance()
            stop_toks = tokenize_directive(stop_seg.text, base_line=stop_seg.line)
            cond_n = self._parse_full_expr(stop_toks[1:])
            body_n, hit = self._parse_top(stoppers=('ELIF', 'ELSEIF', 'ELSE', 'END'))
            cases.append((cond_n, body_n))
        if hit == 'ELSE':
            self._advance()  # consume $ELSE$
            else_body, hit = self._parse_top(stoppers=('END',))
        if hit != 'END':
            raise SyntaxError(f"$IF block at line {line}: expected $END$, got {hit}")
        self._advance()  # consume $END$
        return IfStmt(cases=cases, else_body=else_body, line=line)

    def _parse_foreach(self, line: int, rest: List[Tok]) -> ForeachStmt:
        ts = TokenStream(rest)
        var_name = ts.expect('IDENT').value
        list_expr = parse_expression(ts)
        if not ts.eof():
            raise SyntaxError(f"trailing tokens in $FOREACH at line {line}")
        body, hit = self._parse_top(stoppers=('END',))
        if hit != 'END':
            raise SyntaxError(f"$FOREACH at line {line}: expected $END$")
        self._advance()
        return ForeachStmt(var_name, list_expr, body, line=line)

    def _parse_joineach(self, line: int, rest: List[Tok]) -> JoinEachStmt:
        ts = TokenStream(rest)
        var_name = ts.expect('IDENT').value
        list_expr = parse_expression(ts)
        delim_expr = parse_expression(ts)
        if not ts.eof():
            raise SyntaxError(f"trailing tokens in $JOINEACH at line {line}")
        body, hit = self._parse_top(stoppers=('END',))
        if hit != 'END':
            raise SyntaxError(f"$JOINEACH at line {line}: expected $END$")
        self._advance()
        return JoinEachStmt(var_name, list_expr, delim_expr, body, line=line)

    def _parse_while(self, line: int, rest: List[Tok]) -> WhileStmt:
        cond = self._parse_full_expr(rest)
        body, hit = self._parse_top(stoppers=('END',))
        if hit != 'END':
            raise SyntaxError(f"$WHILE at line {line}: expected $END$")
        self._advance()
        return WhileStmt(cond, body, line=line)

    def _parse_joinwhile(self, line: int, rest: List[Tok]) -> JoinWhileStmt:
        ts = TokenStream(rest)
        cond = parse_expression(ts)
        delim_expr = parse_expression(ts)
        if not ts.eof():
            raise SyntaxError(f"trailing tokens in $JOINWHILE at line {line}")
        body, hit = self._parse_top(stoppers=('END',))
        if hit != 'END':
            raise SyntaxError(f"$JOINWHILE at line {line}: expected $END$")
        self._advance()
        return JoinWhileStmt(cond, delim_expr, body, line=line)

    def _parse_function(self, line: int, rest: List[Tok]) -> FunctionDef:
        ts = TokenStream(rest)
        name = ts.expect('IDENT').value
        if not ts.eof():
            raise SyntaxError(f"trailing tokens in $FUNCTION at line {line}")
        body, hit = self._parse_top(stoppers=('END',))
        if hit != 'END':
            raise SyntaxError(f"$FUNCTION at line {line}: expected $END$")
        self._advance()
        return FunctionDef(name, body, line=line)

    def _parse_error_warning(self, line: int, rest: List[Tok], *, is_error: bool):
        # rest が空なら $ERROR$ / $WARNING$ 形式 (引数なし)
        # 非空なら expression として読む
        arg = None
        if rest:
            arg = self._parse_full_expr(rest)
        body, hit = self._parse_top(stoppers=('END',))
        if hit != 'END':
            raise SyntaxError(f"${'ERROR' if is_error else 'WARNING'} at line {line}: expected $END$")
        self._advance()
        cls = ErrorDir if is_error else WarningDir
        return cls(arg=arg, body=body, line=line)

    def _parse_file(self, line: int, rest: List[Tok]) -> FileDir:
        ts = TokenStream(rest)
        s = ts.expect('STR')
        if not ts.eof():
            raise SyntaxError(f"trailing tokens in $FILE at line {line}")
        return FileDir(path=s.value, line=line)

    # ----- 共通 -----

    def _parse_full_expr(self, toks: List[Tok]):
        ts = TokenStream(toks)
        e = parse_expression(ts)
        if not ts.eof():
            extra = ts.peek()
            raise SyntaxError(f"unexpected trailing tokens: {extra!r}")
        return e


def parse(segments: List[Segment]) -> Document:
    """セグメント列を AST に変換するエントリポイント．"""
    return Parser(segments).parse()

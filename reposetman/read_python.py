import tokenize
import os


def get_comments_list_from_filename(filename, encoding='utf-8'):
    with open(filename, encoding=encoding) as f:
        result = get_comments_list_from_readline(f.readline, filename=filename)
    
    return result


def get_comments_list_from_readline(readline, filename=None):
    comments = []
    # https://stackoverflow.com/questions/34511673/extracting-comments-from-python-source-code

    try:
        for toktype__tok__start__end__line in tokenize.generate_tokens(readline):
            toktype = toktype__tok__start__end__line[0]
            token = toktype__tok__start__end__line[1]
            line = toktype__tok__start__end__line[4]
            if toktype == tokenize.COMMENT:
                comments.append(token.strip('#').strip().strip('.'))
    except tokenize.TokenError:
        print('*** tokenize.TokenError ***')
        show_line_info(filename, line, readline)
    except IndentationError:
        print('*** IndentationError ***')
        show_line_info(filename, line, readline)

    return comments

def show_line_info(filename, line, readline=None):
    print('cwd=', os.getcwd())
    if filename is not None:
        print('filename =', filename)
    elif readline is not None:
        print('readline =', readline)
    print('line = {line}'.format(line=line))


def is_input(filename):
    result = False
    with open(filename, encoding='utf-8') as f:
        try:
            for toktype, tok, start, end, line in tokenize.generate_tokens(f.readline):
                if (tokenize.COMMENT != toktype) and ('input' in tok):
                    result = toktype, tok, start, end, line
                    break
        except tokenize.TokenError:
            print('*** tokenize.TokenError ***')
            show_line_info(filename, line)
        except IndentationError:
            print('*** IndentationError ***')
            show_line_info(filename, line)

    return result

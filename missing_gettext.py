from logilab import astng
from logilab.astng.node_classes import *

from pylint.interfaces import IASTNGChecker
from pylint.checkers import BaseChecker

class MissingGettextChecker(BaseChecker):
    """
    Checks for strings that aren't wrapped in a _ call somewhere
    """
    
    __implements__ = IASTNGChecker

    name = 'missing_gettext'
    msgs = {
        'W9903': ('non-gettext-ed string %r',
                  "There is a raw string that's not passed through gettext"),
        }

    # this is important so that your checker is executed before others
    priority = -1 


    def visit_const(self, node):
        if not isinstance(node.value, str):
            return
        
        if node.value in ['', 'POST']:
            # some whitelisted values unique to us
            return

        string_ok = False
        
        debug = False
        #debug = True
        curr_node = node
        whitelist = [
            # {'shouldignore': 1}
            (Dict,    lambda curr_node, node: node in [x[0] for x in curr_node.items]),

            # dict['shouldignore']
            (Index,   lambda curr_node, node: curr_node.value == node),
            # list_display = [....]
            (Assign,  lambda curr_node, node: len(curr_node.targets) == 1 and hasattr(curr_node.targets[0], 'name') and curr_node.targets[0].name in ['list_display', 'js', 'css', 'fields', 'exclude', 'list_filter', 'list_display_links', 'ordering', 'search_fields', 'actions' ]),

            # Just a random string in the code
            (Discard, lambda curr_node, node: curr_node.value == node),

            # X(attrs={'class': 'somecssclass', 'maxlength': '20'})
            (Keyword, lambda curr_node, node: curr_node.arg == 'attrs' and node in [x[1] for x in curr_node.value.items if x[0].value in ['class', 'maxlength', 'cols', 'rows', 'checked', 'disabled']]),
            (Keyword, lambda curr_node, node: curr_node.arg in ['regex', 'prefix', 'css_class', 'mimetype', 'related_name'] and curr_node.value == node),
            (Keyword, lambda curr_node, node: curr_node.arg in ['input_formats'] and len(curr_node.value.elts) == 1 and curr_node.value.elts[0] == node),
            (Keyword, lambda curr_node, node: curr_node.arg in ['fields'] and node in curr_node.value.elts),
            # something() == 'string'
            (Compare, lambda curr_node, node: node == curr_node.ops[0][1]),
            # 'something' == blah()
            (Compare, lambda curr_node, node: node == curr_node.left),

        ]
        if debug:
            import pdb ; pdb.set_trace()

        # we have a string. Go upwards to see if we have a _ function call
        try:
            while curr_node.parent is not None:
                if debug:
                    print repr(curr_node); print repr(curr_node.as_string()) ; print curr_node.repr_tree()
                if isinstance(curr_node, CallFunc):
                    if not hasattr(curr_node, 'func'):
                        pass
                    elif isinstance(curr_node.func, Getattr):
                        if curr_node.func.attrname in ['has_key', 'pop', 'order_by', 'strftime', 'strptime', 'get', 'select_related', 'values', 'filter', 'values_list']:
                            # known good function call. limit false positives
                            string_ok = True
                            break
                        elif hasattr(curr_node.func.expr, 'name') and curr_node.func.expr.name in ['logging']:
                            # logging.something("should ignore")
                            string_ok = True
                            break
                    elif hasattr(curr_node.func, 'name'):
                        if curr_node.func.name in ['_', 'ungettext', 'ungettext_lazy']:
                            # we're in a _() call
                            string_ok = True
                            break

                        # hasattr(..., 'should ignore')
                        # HttpResponseRedirect('/some/url/shouldnt/care')
                        # first is function name, 2nd is the position the string must be in (none to mean don't care)
                        ok_funcs = [('hasattr', 1), ('HttpResponseRedirect', None), ('render_to_response', 0), ('set_cookie', 0)]
                        for func_name, idx in ok_funcs:
                            if curr_node.func.name == func_name and (idx is None or curr_node.args[idx] == node):
                                string_ok = True
                                break


                for cls, func in whitelist:
                    if isinstance(curr_node, cls) and func(curr_node, node):
                        string_ok = True
                        break

                curr_node = curr_node.parent

        except Exception, e:
            print node, node.as_string()
            print curr_node, curr_node.as_string()
            print e
            import pdb ; pdb.set_trace()
        
        if not string_ok:
            self.add_message('W9903', node=node, args=node.value)

    
def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(MissingGettextChecker(linter))
        


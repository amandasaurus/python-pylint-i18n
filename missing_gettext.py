from logilab import astng
from logilab.astng.node_classes import *

from pylint.interfaces import IASTNGChecker
from pylint.checkers import BaseChecker

import string

def is_number(string):
    """Returns True if this string is a string representation of a number"""
    try:
        float(string)
        return True
    except ValueError:
        return False

def is_child_node(child, parent):
    """Returns True if child is an eventual child node of parent"""
    node = child
    while node is not None:
        if node == parent:
            return True
        node = node.parent
    return False


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
        if not (isinstance(node.value, str) or isinstance(node.value, unicode)):
            return

        # Ignore some strings based on the contents.
        # Each element of this list is a one argument function. if any of them
        # return true for this string, then this string is ignored
        whitelisted_strings = [
            # ignore empty strings
            lambda x : x == '',

            # some strings we use 
            lambda x: x in ['POST', 'agency', 'promoter', 'venue', 'utf-8'],

            # This string is probably used as a key or something, and should be ignored
            lambda x: len(x) > 3 and x.upper() == x,

            # pure number
            is_number,

            # URL, can't be translated
            lambda x: x.startswith("http://") or x.endswith(".html"),
            lambda x: x.startswith("https://") or x.endswith(".html"),
            
            # probably a regular expression
            lambda x: x.startswith("^") and x.endswith("$"),

            # probably a URL fragment
            lambda x: x.startswith("/") and x.endswith("/"),

            # Only has format specifiers and non-letters, so ignore it
            lambda x :not any([z in x.replace("%s", "").replace("%d", "") for z in string.letters]),

            # sending http attachment header
            lambda x: x.startswith("attachment; filename="),

            # sending http header
            lambda x: x.startswith("text/html; charset="),
        ]

        for func in whitelisted_strings:
            if func(node.value):
                return
        

        # Whitelist some strings based on the structure.
        # Each element of this list is a 2-tuple, class and then a 2 arg function.
        # Starting with the current string, and going up the parse tree to the
        # root (i.e. the whole file), for every whitelist element, if the
        # current node is an instance of the first element, then the 2nd
        # element is called with that node and the original string. If that
        # returns True, then this string is assumed to be OK.
        # If any parent node of this string returns True for any of these
        # functions then the string is assumed to be OK
        whitelist = [
            # {'shouldignore': 1}
            (Dict,    lambda curr_node, node: node in [x[0] for x in curr_node.items]),

            # dict['shouldignore']
            (Index,   lambda curr_node, node: curr_node.value == node),

            # list_display = [....]
            # e.g. Django Admin class Meta:...
            (Assign,  lambda curr_node, node: len(curr_node.targets) == 1 and hasattr(curr_node.targets[0], 'name') and curr_node.targets[0].name in ['list_display', 'js', 'css', 'fields', 'exclude', 'list_filter', 'list_display_links', 'ordering', 'search_fields', 'actions', 'unique_together', 'db_table', 'custom_filters', 'search_fields', 'custom_date_list_filters', 'export_fields', 'date_hierarchy' ]),

            # Just a random doc-string-esque string in the code
            (Discard, lambda curr_node, node: curr_node.value == node),

            # X(attrs={'class': 'somecssclass', 'maxlength': '20'})
            (Keyword, lambda curr_node, node: curr_node.arg == 'attrs' and hasattr(curr_node.value, 'items') and node in [x[1] for x in curr_node.value.items if x[0].value in ['class', 'maxlength', 'cols', 'rows', 'checked', 'disabled', 'readonly']]),
            # X(attrs=dict(....))
            (Keyword, lambda curr_node, node: curr_node.arg == 'attrs' and isinstance(curr_node.value, CallFunc) and hasattr(curr_node.value.func, 'name') and curr_node.value.func.name == 'dict' ),
            # x = CharField(default='xxx', related_name='tickets') etc.
            (Keyword, lambda curr_node, node: curr_node.arg in ['regex', 'prefix', 'css_class', 'mimetype', 'related_name', 'default', 'initial', 'upload_to'] and curr_node.value == node),
            (Keyword, lambda curr_node, node: curr_node.arg in ['input_formats'] and len(curr_node.value.elts) == 1 and curr_node.value.elts[0] == node),
            (Keyword, lambda curr_node, node: curr_node.arg in ['fields'] and node in curr_node.value.elts),
            # something() == 'string'
            (Compare, lambda curr_node, node: node == curr_node.ops[0][1]),
            # 'something' == blah()
            (Compare, lambda curr_node, node: node == curr_node.left),

            # Try to exclude queryset.extra(something=[..., 'some sql',...]
            (CallFunc, lambda curr_node, node: curr_node.func.attrname in ['extra'] and any(is_child_node(node, x) for x in curr_node.args)),

            # Queryset functions, queryset.order_by('shouldignore')
            (CallFunc, lambda curr_node, node: isinstance(curr_node.func, Getattr) and curr_node.func.attrname in ['has_key', 'pop', 'order_by', 'strftime', 'strptime', 'get', 'select_related', 'values', 'filter', 'values_list']),
             # logging.info('shouldignore')
            (CallFunc, lambda curr_node, node: curr_node.func.expr.name in ['logging']),

                
            # hasattr(..., 'should ignore')
            # HttpResponseRedirect('/some/url/shouldnt/care')
            # first is function name, 2nd is the position the string must be in (none to mean don't care)
            (CallFunc, lambda curr_node, node: curr_node.func.name in ['hasattr', 'getattr'] and curr_node.args[1] == node),
            (CallFunc, lambda curr_node, node: curr_node.func.name in ['HttpResponseRedirect', 'HttpResponse']),
            (CallFunc, lambda curr_node, node: curr_node.func.name == 'set_cookie' and curr_node.args[0] == node),
            (CallFunc, lambda curr_node, node: curr_node.func.name in ['ForeignKey', 'OneToOneField'] and curr_node.args[0] == node),
        ]

        string_ok = False
        
        debug = False
        #debug = True
        curr_node = node
        if debug:
            import pdb ; pdb.set_trace()

        # we have a string. Go upwards to see if we have a _ function call
        try:
            while curr_node.parent is not None:
                if debug:
                    print repr(curr_node); print repr(curr_node.as_string()) ; print curr_node.repr_tree()
                if isinstance(curr_node, CallFunc):
                    if hasattr(curr_node, 'func') and hasattr(curr_node.func, 'name'):
                        if curr_node.func.name in ['_', 'ungettext', 'ungettext_lazy']:
                            # we're in a _() call
                            string_ok = True
                            break

                # Look at our whitelist
                for cls, func in whitelist:
                    if isinstance(curr_node, cls):
                        try:
                            # Ignore any errors from here. Otherwise we have to
                            # pepper the whitelist with loads of defensive
                            # hasattrs, which increase bloat
                            if func(curr_node, node):
                                string_ok = True
                                break
                        except:
                            pass

                curr_node = curr_node.parent

        except Exception, e:
            print node, node.as_string()
            print curr_node, curr_node.as_string()
            print e
            import pdb ; pdb.set_trace()
        
        if not string_ok:
            # we've gotten to the top of the code tree / file level and we
            # haven't been whitelisted, so add an error here
            self.add_message('W9903', node=node, args=node.value)

    
def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(MissingGettextChecker(linter))
        


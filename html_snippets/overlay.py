def html_auto_blend_last_child(html):
    head = """
<style>
.auto_blend {
  text-align: left;
  position: relative;
}
.auto_blend *:last-child {
  position: absolute;
  top: 0;
  left: 0;
  animation: fade 2s infinite alternate;
}
@keyframes fade {
  0% { opacity: 1; }
  100% { opacity: 0; }
}
</style>
"""
    body = f'<div class="auto_blend">\n{html}\n</div>'
    return head, body


def html_overlay_hide_on_hover(html):
    head = """
<style>
  .overlay_hide_on_hover {
    text-align: left;
    position: relative;
  }
  .overlay_hide_on_hover *:last-child {
    position: absolute;
    top: 0;
    left: 0;
    opacity: 1;
  }
  .overlay_hide_on_hover *:last-child:hover {
      opacity: 0.1;
  }
</style>
"""
    body = f'<div class="overlay_hide_on_hover">\n{html}\n</div>'
    return head, body


def html_auto_show_hide_last_child(html):
    head = """
<style>
.auto_show_hide {
  text-align: left;
  position: relative;
}
.auto_show_hide *:last-child {
  position: absolute;
  top: 0;
  left: 0;
  animation: show_hide 2s infinite alternate;
}
@keyframes show_hide {
  0% { opacity: 1; }
  49% { opacity: 1; }
  51% { opacity: 0; }
  100% { opacity: 0; }
}
</style>
"""
    body = f'<div class="auto_show_hide">\n{html}\n</div>'
    return head, body


def html_frame_sequence(elements:list, frame_time=.5, ):
    """Note that this function generates the same head for a set of len(elemenst) and frame_time.
    You will not be able, however, to have a single HTML with animations of the same number
    of images but with different duration. You should also avoid adding the head for each animation
    of equal length."""

    head = """
    <style>
    .auto_show_hideNUM {
      position: relative;
    }
    .auto_show_hideNUM > * {
      position: absolute;
      top: 0;
      left: 0;
      opacity: 0;
    }
    @keyframes show_hideNUM {
    FRAMES
    }
    
    NTH_CHILDREN</style>
    """

    NUM = len(elements)
    pct = round(100 / NUM, 2)
    FRAMES =  "0% { opacity: 1; }\n" + \
          f"{pct}" + "% { opacity: 1; }\n" + \
          f"{pct+1}" + "% { opacity: 0; }\n" + \
          "100% { opacity: 0; }"
    NTH_CHILDREN = '.auto_show_hideNUM *:first-child {\n' + \
               '  opacity: 1;\n' + \
               '}\n'
    for idx in range(1, NUM + 1):
        NTH_CHILDREN += '.auto_show_hideNUM *:nth-child(' + str(idx) + ') {\n' + \
                        '  animation: show_hideNUM  TIME infinite;\n' + \
                        '  animation-delay: ' + str(frame_time*idx) + 's;\n' + \
                        '}\n'

    head = head.replace("NTH_CHILDREN", str(NTH_CHILDREN))
    head = head.replace("NUM", str(NUM)).replace("FRAMES", FRAMES).replace("TIME", str(NUM*frame_time)+'s')

    body = f'<div class="auto_show_hide{NUM}">\n'
    body += "\n".join(elements)
    body += '\n</div>\n'
    
    return head, body

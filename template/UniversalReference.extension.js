var suffix = 'UniversalReferenceTransform';
var transforms = null;

var getTransforms = function (model) {
  if (transforms === null) {
    var tokens = model.__global || {};
    transforms = Object.keys(tokens).filter(function (key) {
      return key.length > suffix.length && key.slice(-suffix.length) === suffix;
    }).map(function (key) {
      var transform = require('./' + tokens[key]);
      if (!transform) throw new Error('Cannot find ' + tokens[key] + ', registered as ' + key + ' in token.json.');
      return transform;
    });
  }
  return transforms;
}

exports.preTransform = function (model) {
  model.yamlmime = 'ManagedReference';
  getTransforms(model).forEach(function (transform) {
    if (transform.preTransform) model = transform.preTransform(model);
  });
  return model;
}

exports.postTransform = function (model) {
  var visit = function (trees) {
    if (!trees) return;
    trees.forEach(function (tree) {
      if (tree.lang && tree.value) {
        visit(tree.value);
        return;
      }
      if (!tree.inheritance || tree.inheritance.length === 0) {
        tree.inheritance = [];
      } else {
        visit(tree.inheritance);
      }
    });
  };
  visit(model.inheritance);

  var sourceHref = function (item) {
    var source = item.source;
    if (Array.isArray(source)) {
      source = source.length > 0 ? source[0].value : null;
    }
    return source && source.href ? source.href : '';
  };
  model.sourceurl = model.sourceurl || sourceHref(model);
  (model.children || []).forEach(function (group) {
    (group.children || []).forEach(function (item) {
      item.sourceurl = item.sourceurl || sourceHref(item);
      item.summary = item.summary || '';
      item.conceptual = item.conceptual || '';
      item.remarks = item.remarks || '';
    });
  });

  var firstParagraph = function (html) {
    var match = typeof html === 'string' ? html.match(/^\s*<p[\s>][\s\S]*?<\/p>\s*/) : null;
    return match ? match[0] : html;
  };
  if (model.isNamespace) {
    (model.children || []).forEach(function (group) {
      if (group.isEmbedded) return;
      (group.children || []).forEach(function (item) {
        item.summary = firstParagraph(item.summary);
      });
    });
  }

  var escapeHtml = function (text) {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  };
  if (model.isEnum) {
    var rows = [];
    (model.children || []).forEach(function (group) {
      if (!group.inField) return;
      group.children = (group.children || []).filter(function (item) {
        var content = item.syntax && item.syntax.content;
        var declaration = content && content.length > 0 ? content[0].value : '';
        var separator = declaration.indexOf(' = ');
        if (separator < 0) return true;
        rows.push({
          id: item.id,
          uid: item.uid,
          cells: [
            { html: '<code>' + escapeHtml(declaration.slice(0, separator)) + '</code>' },
            { html: escapeHtml(declaration.slice(separator + 3)) },
            { html: item.summary }
          ]
        });
        return false;
      });
    });
    if (rows.length > 0) {
      var global = model.__global || {};
      var columns = [{ header: global.name || 'Name' }, { header: 'Value' }, { header: global.description || 'Description' }];
      if (rows.every(function (row) { return !row.cells[2].html; })) {
        columns.pop();
        rows.forEach(function (row) { row.cells.pop(); });
      }
      model.children = model.children.filter(function (group) { return group.children.length > 0; });
      model.tableReference = {
        tables: [{ level: 2, id: 'values', heading: 'Values', intro: '', columns: columns, rows: rows }]
      };
    }
  }

  getTransforms(model).forEach(function (transform) {
    if (transform.postTransform) model = transform.postTransform(model);
  });

  var reference = model.tableReference;
  if (reference && reference.conceptualHeading) {
    reference.conceptualId = reference.conceptualHeading.toLowerCase().replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '-');
  }
  return model;
}

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

  getTransforms(model).forEach(function (transform) {
    if (transform.postTransform) model = transform.postTransform(model);
  });
  return model;
}

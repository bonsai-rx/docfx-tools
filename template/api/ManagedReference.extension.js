// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.

// Define Bonsai operator types in documentation by checking for an explicit Category tag. If the class does not provide one,
// check the inheritance tree of the class. 
function defineOperatorType(model){
  const checkForCategory = (category) => model.syntax?.content[0].value.includes(`[WorkflowElementCategory(ElementCategory.${category})]`);
  const checkInheritance = (inheritance) => model.inheritance?.some(inherited => inherited.uid.includes(inheritance));

  source = checkForCategory('Source') || checkInheritance('Bonsai.Source');
  sink = checkForCategory('Sink') || checkInheritance('Bonsai.Sink') || checkInheritance('Bonsai.IO.StreamSink') || checkInheritance('Bonsai.IO.FileSink');
  combinator = checkForCategory('Combinator') || checkInheritance('Bonsai.Combinator') || checkInheritance('Bonsai.WindowCombinator');
  transform = checkForCategory('Transform') || checkInheritance('Bonsai.Transform') || checkInheritance('Bonsai.Transform');
  workflow = checkForCategory('Workflow')

  let operatorType = {}
  operatorType.type = sink ? 'sink' : source ? 'source' : transform ? 'transform' : combinator ? 'combinator' : workflow ? 'workflow' : false ; 

  return operatorType;
}

// This function is important for stripping the extra line that is present in some fields
// replace last instance of '<p' with '<p style="margin-bottom:0;"'
function removeBottomMargin(str) {
  return str
    .split('').reverse().join('')
    .replace('<p'.split('').reverse().join(''), '<p style="margin-bottom:0;"'.split('').reverse().join(''))
    .split('').reverse().join('');
}

// Strip IObservable and replace 'TSource' with 'Anything' 
// Added a null check to return an empty string to avoid undefined errors in new refactored code
// Added links to Bonsai user guide on operators 
function replaceIObservableAndTSource(str){
  const observableLink = '<a href="https://bonsai-rx.org/docs/articles/observables.html">Observable</a>'
  if (!str) {
    return '';
  }
  else if (str.includes('IGroupedObservable')){
    const re = new RegExp('<a.*IGroupedObservable.*&lt;');
    str = str.replace(re, '').replace('&gt;','').replace('&gt;','').replace('TSource', observableLink);
  }
  else if (str.includes('IObservable')){
    const re = new RegExp('<a.*IObservable.*&lt;');
    str = str.replace(re, '').replace('&gt;','').replace('TSource', observableLink);
    // can't combine re and '&gt;' into the same regex and do replaceAll because some classes have have two '&gt' in which case one of them is necessary
  }
  return str;
}

// this function is a revised version of cris's refactored function that restores the original values (specname, description)
// which were removed
function defineInputsAndOutputs(model){
  overloads = model.children
    .filter(child => child.name[0].value.includes('Process') || child.name[0].value.includes('Generate'))
    .map(child => ({
      'description': [child.summary, child.remarks].join(''),
      'input': {
        'specName': replaceIObservableAndTSource(child.syntax?.parameters[0].type.specName[0].value),
        'description': removeBottomMargin([child.syntax?.parameters[0].description, child.syntax?.parameters[0].remarks].join(''))
       },
      'output': {
        'specName': replaceIObservableAndTSource(child.syntax.return.type.specName[0].value),
        'description': removeBottomMargin([child.syntax.return.description, child.syntax.return.remarks].join('')),
      }
    }))
    .map(item => {
      // Remove input if it's empty
      if (!item.input.specName && !item.input.description) {
        delete item.input;
      }
      return item;
    });
  return overloads;
}

// extracts enums so that they can be expanded in the properties table
function processChildProperty(child, sharedModel) {
  const enumFields = sharedModel[`~/api/${child.syntax.return.type.uid}.yml`]?.type === 'enum' ?
    extractEnumData(sharedModel[`~/api/${child.syntax.return.type.uid}.yml`]) :
    [];
  return {
    'name': child.name[0].value,
    'type': child.syntax.return.type.specName[0].value,
    'propertyDescription': {
      'text': enumFields.length > 0
        ? [child.summary, child.remarks].join('')
        : removeBottomMargin([child.summary, child.remarks].join('')),
      'hasEnum': enumFields.length > 0,
      'enum': enumFields,
    }
  }
}

function extractPropertiesData(model, sharedModel) {
  return model?.children
    .filter(child => child.type === 'property' && child.syntax)
    .map(child => processChildProperty(child, sharedModel));
}

function extractPropertiesFromInheritedMembersData(model, sharedModel) {
  // Ensure inheritedMembers exists and is an array before filtering
  // Important for IncludeWorkflow operators which currently do not have any inherited members
  if (!Array.isArray(model.inheritedMembers)) {
    return [];
  }
  return model.inheritedMembers
  .filter(inheritedMember => inheritedMember.type === 'property')
  .map(inheritedMember => {
    return processChildProperty(
      sharedModel[`~/api/${inheritedMember.parent}.yml`].children.find(inheritedMemberChild => inheritedMemberChild.uid === inheritedMember.uid),
      sharedModel
    );
  });
}


// Properties are usually already listed in declaration order which mirrors Bonsai UI.
// However a bug in docfx messes up properties that have a numeric endvalue ie Device10 < Device2
// and this function fixes that.
function sortPropertiesData(properties) {
  return properties.sort((a, b) => {
    const regex = /\D+|\d+$/g;

    // Extract parts for property 'a'
    const [prefixA, numberA] = a.name.match(regex);
    const numA = Number(numberA);

    // Extract parts for property 'b'
    const [prefixB, numberB] = b.name.match(regex);
    const numB = Number(numberB);

    // If prefix is the same, compare numbers
    if (prefixA == prefixB) {
      return numA - numB;
    }
  });
}

// While enum fields can be accessed directly using the mustache template, this function is
// still important for stripping the extra line that is present in the summary/remarks field
function extractEnumData(model){
  return model.children
    .filter(child => child.type === 'field')
    .map(child => ({
      'field&value': child.syntax.content[0].value,
      'enumDescription': removeBottomMargin([child.summary, child.remarks].join(''))
    }));
}

/**
 * This method will be called at the start of exports.transform in ManagedReference.html.primary.js
 */
exports.preTransform = function (model) {
  
  model.bonsai = {};
  
  model.bonsai.description = [model.summary, model.remarks].join('');

  operatorType = defineOperatorType(model);

  if (operatorType.type){
    model.bonsai.operatorType = operatorType.type;
    model.bonsai.showWorkflow = true
    operators = defineInputsAndOutputs(model);
    model.bonsai.operators = operators;
  }

  if (model.type === 'class') {
    properties = sortPropertiesData([
      ...extractPropertiesData(model, model.__global._shared),
      ...extractPropertiesFromInheritedMembersData(model, model.__global._shared),
    ]);
    if (properties.length > 0){
      model.bonsai.hasProperties = true;
      model.bonsai.properties = properties
    }
  }

  else if (model.type === 'enum') {
    model.bonsai.enumFields = extractEnumData(model);
    model.bonsai.hasEnumFields = true;
  }
  return model;
}

/**
 * This method will be called at the end of exports.transform in ManagedReference.html.primary.js
 */
exports.postTransform = function (model) {
  return model;
}
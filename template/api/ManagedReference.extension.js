// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.

var BonsaiCommon = require('./BonsaiCommon.js')

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
// Consider replace "Anything" with "Observable" or "Any Observable" with a link to the observable guide
function replaceIObservableAndTSource(str){
  if (!str) {
    return '';
  }
  else if (str.includes('IGroupedObservable')){
    const re = new RegExp('<a.*IGroupedObservable.*&lt;');
    str = str.replace(re, '').replace('&gt;','').replace('&gt;','').replace('TSource', 'Anything');
  }
  else if (str.includes('IObservable')){
    const re = new RegExp('<a.*IObservable.*&lt;');
    str = str.replace(re, '').replace('&gt;','').replace('TSource', 'Anything');
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
  return overloads;
}

// compile list of properties
function defineProperties(model){
  properties = [];
  if (model.children){
    const childrenLength = model.children.length;
    for (let i = 0; i < childrenLength; i++){
      if (model.children[i].type === 'property'){

        // This section adds enum fields and values to the property table if the property is an enum
        // However doesnt always work (In Pulsepal Repo - Outputchannel enum doesnt show sometimes but the others do)
        // Bug present in original template so need to troubleshoot
        // Nice to have I think but not critical.
        potentialEnumYml = '~/api/' + model['children'][i].syntax.return.type.uid + '.yml';
        let enumFields = [];
        if (model['__global']['_shared'][potentialEnumYml] && (model['__global']['_shared'][potentialEnumYml]['type'] === 'enum')){
          enumFields = defineEnumFields(model['__global']['_shared'][potentialEnumYml]);
        }
        if (enumFields.length > 0){
          properties.push({
            'name': model.children[i].name[0].value, 
            'type': model.children[i].syntax.return.type.specName[0].value, 
            'description': removeBottomMargin([model.children[i].summary, model.children[i].remarks].join('')),
            'enumFields': enumFields,
            'hasEnum': true
          });
        }
        // This adds the rest of the non-enum properties normally
        else { 
          properties.push({
            'name': model.children[i].name[0].value, 
            'type': model.children[i].syntax.return.type.specName[0].value, 
            'description': removeBottomMargin([model.children[i].summary, model.children[i].remarks].join(''))
          });
        }
      }
    }
  }
  // This adds properties that belong to the members that it inherits (and which show up in the Bonsai side panel)
  // On a default docfx website they dont show, so its pretty important.
  if (model.inheritedMembers){
    const inheritedMembersLength = model.inheritedMembers.length;
    for (let i = 0; i < inheritedMembersLength; i++){
      if (model.inheritedMembers[i].type && (model.inheritedMembers[i].type === 'property')){
        let inheritedMemberYml = '~/api/' + model.inheritedMembers[i].parent + '.yml';
        if (model['__global']['_shared'][inheritedMemberYml]['children']){
          let inheritedMemberChildrenLength = model['__global']['_shared'][inheritedMemberYml]['children'].length;
          for (let j =  0; j < inheritedMemberChildrenLength; j++){
            if (model.inheritedMembers[i].uid === model['__global']['_shared'][inheritedMemberYml]['children'][j].uid){
              properties.push(
                {'name': model.inheritedMembers[i].name[0].value, 
                'type': model['__global']['_shared'][inheritedMemberYml]['children'][j].syntax.return.type.specName[0].value, 
                'description':  removeBottomMargin([model['__global']['_shared'][inheritedMemberYml]['children'][j].summary, 
                                                    model['__global']['_shared'][inheritedMemberYml]['children'][j].remarks].join(''))
              });
            }
          }
        }
      }
    }
  }
  return properties;
}

// Properties are usually already listed in declaration order which mirrors Bonsai UI.
// However a bug in docfx messes up properties that have a numeric endvalue ie Device10 < Device2
// and this function fixes that.
function sortProperties(properties) {
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
function defineEnumFields(model){
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

  operatorType = BonsaiCommon.defineOperatorType(model);

  if (operatorType.type){
    model.bonsai.operatorType = operatorType.type;
  }

  if (operatorType.showWorkflow) {
    model.bonsai.showWorkflow = operatorType.showWorkflow;
  }
  
  operators = defineInputsAndOutputs(model);
  if (operators.length > 0){
    model.bonsai.operators = operators;
  }

  properties = defineProperties(model);
  if (properties.length > 0){
    model.bonsai.hasProperties = true;
    model.bonsai.properties = sortProperties(properties);
  }

  enumFields = defineEnumFields(model);
  if (enumFields.length > 0){
    model.bonsai.hasEnumFields = true;
    model.bonsai.enumFields = enumFields;
  }

  return model;
}

/**
 * This method will be called at the end of exports.transform in ManagedReference.html.primary.js
 */
exports.postTransform = function (model) {
  return model;
}